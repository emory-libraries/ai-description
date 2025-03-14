# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'aws-sdk-sqs'
require 'aws-sdk-ecs'

# Constants
AWS_REGION = ENV['AWS_REGION']
ECS_CLUSTER_NAME = ENV['ECS_CLUSTER_NAME']
ECS_TASK_DEFINITION_ARN = ENV['ECS_TASK_DEFINITION_ARN']
ECS_TASK_FAMILY_NAME = ECS_TASK_DEFINITION_ARN.split('/')[-1].split(':')[0]
SQS_QUEUE_URL = ENV['SQS_QUEUE_URL']
CORS_HEADERS = {
  'Access-Control-Allow-Origin' => '*',
  'Access-Control-Allow-Headers' => '*',
  'Access-Control-Allow-Methods' => '*',
  'Access-Control-Allow-Credentials' => true
}

# Initialize AWS clients globally
$sqs = Aws::SQS::Client.new(region: AWS_REGION)
$ecs_client = Aws::ECS::Client.new(region: AWS_REGION)

# Set up logging
$logger = Logger.new($stdout)
$logger.level = Logger::INFO

def get_ecs_status(cluster_name, task_family_name)
  running_tasks = $ecs_client.list_tasks(cluster: cluster_name, family: task_family_name, desired_status: 'RUNNING')
  return 'Active' unless running_tasks.task_arns.empty?

  'Inactive'
end

def get_queue_length(queue_url)
  # Get queue attributes
  response = $sqs.get_queue_attributes(
    queue_url: queue_url,
    attribute_names: ['ApproximateNumberOfMessages']
  )

  # Extract the values
  response.attributes['ApproximateNumberOfMessages'].to_i
end

def create_response(status_code, body)
  {
    statusCode: status_code,
    body: body.to_json,
    headers: CORS_HEADERS
  }
end

def handler(event:, context:)
  $logger.info("Getting status of ECS cluster #{ECS_CLUSTER_NAME}")
  ecs_status = get_ecs_status(
    ECS_CLUSTER_NAME, # Pass as direct argument instead of named parameter
    ECS_TASK_FAMILY_NAME # Pass as direct argument instead of named parameter
  )
  queue_length = get_queue_length(SQS_QUEUE_URL)

  # Return success response
  response = {
    ecs_status: ecs_status,
    queue_length: queue_length
  }
  create_response(200, response)
rescue StandardError => e
  $logger.error("Unexpected error: #{e}")
  $logger.error(e.backtrace.join("\n"))
  create_response(500, { error: 'Internal server error' })
end
