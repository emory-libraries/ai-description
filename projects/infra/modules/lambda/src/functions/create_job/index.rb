# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'aws-sdk-dynamodb'
require 'aws-sdk-sqs'
require 'aws-sdk-ecs'
require 'aws-sdk-s3'
require 'uri'

# Load environment variables
AWS_REGION = ENV['AWS_REGION']
WORKS_TABLE_NAME = ENV['WORKS_TABLE_NAME']
SQS_QUEUE_URL = ENV['SQS_QUEUE_URL']
ECS_CLUSTER_NAME = ENV['ECS_CLUSTER_NAME']
ECS_TASK_DEFINITION_ARN = ENV['ECS_TASK_DEFINITION_ARN']
ECS_TASK_FAMILY_NAME = ECS_TASK_DEFINITION_ARN.split('/').last.split(':').first
ECS_CONTAINER_NAME = ENV['ECS_CONTAINER_NAME']
SUBNET_IDS = ENV['ECS_SUBNET_IDS'].split(',')
SECURITY_GROUP_IDS = ENV['ECS_SECURITY_GROUP_IDS'].split(',')

# Configs
CORS_HEADERS = {
  'Access-Control-Allow-Origin' => '*',
  'Access-Control-Allow-Headers' => '*',
  'Access-Control-Allow-Methods' => '*',
  'Access-Control-Allow-Credentials' => true
}

RUN_TASK_KWARGS = {
  cluster: ECS_CLUSTER_NAME,
  task_definition: ECS_TASK_DEFINITION_ARN,
  launch_type: 'FARGATE',
  network_configuration: {
    awsvpc_configuration: {
      subnets: SUBNET_IDS,
      security_groups: SECURITY_GROUP_IDS,
      assign_public_ip: 'DISABLED'
    }
  },
  overrides: {
    container_overrides: [
      {
        name: ECS_CONTAINER_NAME,
        environment: [{ name: 'JOB_ID' }]
      }
    ]
  }
}

# Other constants
JOB_NAME = 'job_name'
JOB_TYPE = 'job_type'
WORKS = 'works'
WORK_ID = 'work_id'
IMAGE_S3_URIS = 'image_s3_uris'
CONTEXT_S3_URI = 'context_s3_uri'
ORIGINAL_METADATA_S3_URI = 'original_metadata_s3_uri'
WORK_STATUS = 'work_status'

# Initialize AWS clients
$dynamodb = Aws::DynamoDB::Resource.new(region: AWS_REGION)
$sqs = Aws::SQS::Client.new(region: AWS_REGION)
$ecs_client = Aws::ECS::Client.new(region: AWS_REGION)
$s3_client = Aws::S3::Client.new(region: AWS_REGION)

# Set up logging
$logger = Logger.new($stdout)
$logger.level = Logger::INFO

def s3_path_to_file_list(s3_path_uri, recursive=true)
  # Parse the S3 URI
  parsed_uri = URI.parse(s3_path_uri)
  if parsed_uri.scheme != 's3'
    raise "Not a valid S3 URI: #{s3_path_uri}"
  end

  bucket = parsed_uri.host

  # Remove leading slash if present
  key = parsed_uri.path.sub(/^\//, '')

  # Check if the path exists directly as an object (file)
  begin
    $s3_client.head_object(bucket: bucket, key: key)
    # If we get here, it's a file that exists
    return [s3_path_uri]
  rescue Aws::S3::Errors::NotFound
    # If not found, we'll treat it as a folder
  rescue => e
    # For any other error, re-raise
    raise e
  end

  # If we get here, the path doesn't exist as a direct object, so treat it as a folder
  # Ensure the path ends with a slash to denote a folder
  folder_prefix = key.end_with?('/') ? key : "#{key}/"

  result_uris = []

  # List objects with the folder prefix
  begin
    continuation_token = nil
    loop do
      list_options = {
        bucket: bucket,
        prefix: folder_prefix,
        continuation_token: continuation_token
      }

      response = $s3_client.list_objects_v2(list_options)

      if response.contents
        response.contents.each do |obj|
          obj_key = obj.key

          # Skip the folder object itself
          next if obj_key == folder_prefix

          # If not recursive, skip objects in subfolders
          next if !recursive && obj_key.sub(folder_prefix, '').include?('/')

          result_uris << "s3://#{bucket}/#{obj_key}"
        end
      end

      # Continue if there are more objects
      break unless response.is_truncated
      continuation_token = response.next_continuation_token
    end
  rescue => e
    $logger.error("Error listing objects: #{e.message}")
    raise e
  end

  # If no files were found and the original path doesn't end with a slash,
  # it might be a file pattern (like a prefix for filtering)
  if result_uris.empty? && !key.end_with?('/')
    begin
      continuation_token = nil
      loop do
        list_options = {
          bucket: bucket,
          prefix: key,
          continuation_token: continuation_token
        }

        response = $s3_client.list_objects_v2(list_options)

        if response.contents
          response.contents.each do |obj|
            result_uris << "s3://#{bucket}/#{obj.key}"
          end
        end

        # Continue if there are more objects
        break unless response.is_truncated
        continuation_token = response.next_continuation_token
      end
    rescue => e
      $logger.error("Error listing objects with prefix: #{e.message}")
      raise e
    end
  end

  result_uris.sort
end

def expand_s3_uris_to_files(uri_list, recursive=true)
  all_files = []

  # Process each URI sequentially instead of in parallel
  uri_list.each do |uri|
    begin
      files = s3_path_to_file_list(uri, recursive)
      all_files.concat(files) if files
    rescue => e
      $logger.error("Error processing URI: #{e.message}")
      raise e
    end
  end

  # Remove any duplicates
  all_files.uniq
end

def validate_request_body(body)
  job_keys = [JOB_NAME, JOB_TYPE, WORKS]
  job_keys_present = job_keys.map { |key| body.key?(key) }

  if job_keys_present.any? && !job_keys_present.all?
    msg = "Request body requires the following keys: #{job_keys}. Request body keys received: #{body.keys}"
    $logger.warn(msg)
    raise msg
  end
end

def job_exists(table, job_name)
  response = table.query(
    key_condition_expression: "#{JOB_NAME} = :job_name",
    expression_attribute_values: {
      ':job_name' => job_name
    },
    limit: 1
  )
  response.items.any?
end

def create_response(status_code, body)
  {
    statusCode: status_code,
    body: body.to_json,
    headers: CORS_HEADERS
  }
end

def create_ecs_task(run_task_kwargs)
  # Check for running tasks
  running_tasks = $ecs_client.list_tasks(
    cluster: ECS_CLUSTER_NAME,
    family: ECS_TASK_FAMILY_NAME,
    desired_status: 'RUNNING'
  )

  if !running_tasks.task_arns.empty?
    message = "A task is already running. No new task will be started."
    $logger.warn(message)
    return message
  end

  # If no task is running, start a new one
  $logger.info("Running task")
  $logger.debug("Task kwargs: #{run_task_kwargs.to_json}")
  response = $ecs_client.run_task(run_task_kwargs)
  message = "New ECS task #{response.tasks[0].task_arn} started successfully"
  $logger.info(message)
  message
end

def create_job(job_name, job_type, works)
  table = $dynamodb.table(WORKS_TABLE_NAME)

  # Check if job already exists
  if job_exists(table, job_name)
    msg = "Job with name '#{job_name}' already exists"
    $logger.error(msg)
    raise msg
  end

  works.each do |work|
    work_id = work[WORK_ID]
    image_s3_uris = work[IMAGE_S3_URIS]
    context_s3_uri = work[CONTEXT_S3_URI]
    original_metadata_s3_uri = work[ORIGINAL_METADATA_S3_URI]

    # Add work item to SQS queue
    sqs_message = {
      JOB_NAME => job_name,
      WORK_ID => work_id
    }
    $sqs.send_message(
      queue_url: SQS_QUEUE_URL,
      message_body: sqs_message.to_json
    )
    $logger.debug("Successfully added job=#{job_name} work=#{work_id} to SQS")

    # Put pending work item in DynamoDB
    ddb_work_item = {
      JOB_NAME => job_name,
      JOB_TYPE => job_type,
      WORK_ID => work_id,
      IMAGE_S3_URIS => expand_s3_uris_to_files(image_s3_uris),
      CONTEXT_S3_URI => context_s3_uri,
      ORIGINAL_METADATA_S3_URI => original_metadata_s3_uri,
      WORK_STATUS => "IN QUEUE"
    }

    # Remove nil values to avoid DynamoDB issues
    ddb_work_item.delete_if { |_, v| v.nil? }

    table.put_item(item: ddb_work_item)
    $logger.debug("Successfully added job=#{job_name} work=#{work_id} to DynamoDB")
  end
  $logger.info("Successfully added all works for job=#{job_name} to SQS and DynamoDB")
end

# This is the entry point for AWS Lambda
def handler(event:, context:)
  begin
    response_message = {}

    # Load args from event
    body = JSON.parse(event['body'])

    # Job creation
    if body.key?(JOB_NAME) && body.key?(JOB_TYPE) && body.key?(WORKS)
      begin
        validate_request_body(body)
        create_job(
          body[JOB_NAME],
          body[JOB_TYPE],
          body[WORKS]
        )
        response_message['job_creation'] = 'Success'
      rescue StandardError => e
        response_message['job_creation'] = "Failed: #{e.message}"
      end
    else
      response_message['job_creation'] = 'No job arguments provided'
    end

    # ECS task creation
    begin
      ecs_message = create_ecs_task(RUN_TASK_KWARGS)
      response_message['ecs_task_creation'] = ecs_message
    rescue StandardError => e
      response_message['ecs_task_creation'] = "Failed: #{e.message}"
    end

    create_response(200, response_message)
  rescue => e
    $logger.error("Unexpected error: #{e.message}\n#{e.backtrace.join("\n")}")
    create_response(500, { 'error' => 'Internal server error' })
  end
end
