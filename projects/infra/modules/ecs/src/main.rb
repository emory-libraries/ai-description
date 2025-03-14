# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# frozen_string_literal: true

require 'aws-sdk-s3'
require 'aws-sdk-sqs'
require 'aws-sdk-dynamodb'
require 'json'
require 'logger'

require 'image_captioning_assistant'

# Constants
AWS_REGION = ENV['AWS_REGION']
WORKS_TABLE_NAME = ENV['WORKS_TABLE_NAME']
SQS_QUEUE_URL = ENV['SQS_QUEUE_URL']
UPLOADS_BUCKET_NAME = ENV['UPLOADS_BUCKET_NAME']

# Configure AWS clients properly for Ruby
S3_KWARGS = {
  region: AWS_REGION,
  # In Ruby SDK, v4 is the default signature version, no need to specify
  force_path_style: false
}

LLM_KWARGS = {
  region: AWS_REGION,
  retry_limit: 1,
  retry_mode: 'standard'
}

RESIZE_KWARGS = {
  max_dimension: 2048,
  jpeg_quality: 95
}

# Field names
JOB_NAME = 'job_name'
JOB_TYPE = 'job_type'
WORK_ID = 'work_id'
IMAGE_S3_URIS = 'image_s3_uris'
CONTEXT_S3_URI = 'context_s3_uri'
ORIGINAL_METADATA_S3_URI = 'original_metadata_s3_uri'
WORK_STATUS = 'work_status'

# Set up logging
$logger = Logger.new($stdout)
$logger.level = Logger::INFO
$logger.formatter = proc do |severity, datetime, _progname, msg|
  "#{datetime} - #{severity} - #{msg}\n"
end

# Initialize AWS clients
$s3 = Aws::S3::Client.new(S3_KWARGS)
$sqs = Aws::SQS::Client.new(region: AWS_REGION)
$dynamodb = Aws::DynamoDB::Resource.new(region: AWS_REGION)
$table = $dynamodb.table(WORKS_TABLE_NAME)

def get_work_details(job_name, work_id)
  response = $table.get_item(
    key: { JOB_NAME => job_name, WORK_ID => work_id }
  )

  raise "No item found for job_name=#{job_name}, work_id=#{work_id}" if response.item.nil?

  response.item
rescue Aws::DynamoDB::Errors::ServiceError => e
  $logger.error("Error retrieving item from DynamoDB: #{e}")
  raise
end

def update_dynamodb_item(job_name:, work_id:, update_data: nil, status: nil)
  # Start with empty update parts
  update_expression_parts = []
  expression_attribute_names = {}
  expression_attribute_values = {}

  # Add status update if provided
  if status
    update_expression_parts << '#status = :status'
    expression_attribute_names['#status'] = WORK_STATUS
    expression_attribute_values[':status'] = status
  end

  # Add field updates from update_data if provided
  if update_data
    update_data.each do |key, value|
      update_expression_parts << "##{key} = :#{key}"
      expression_attribute_names["##{key}"] = key
      expression_attribute_values[":#{key}"] = value
    end
  end

  # If nothing to update, return early
  if update_expression_parts.empty?
    $logger.warn("No updates provided for job=#{job_name}, work=#{work_id}")
    return
  end

  # Create the full update expression
  update_expression = 'SET ' + update_expression_parts.join(', ')

  # Perform the update
  $table.update_item(
    key: { JOB_NAME => job_name, WORK_ID => work_id },
    update_expression: update_expression,
    expression_attribute_names: expression_attribute_names,
    expression_attribute_values: expression_attribute_values
  )

  # Log appropriate message based on what was updated
  log_message = "Updated DynamoDB item for job=#{job_name}, work=#{work_id}"
  log_message += " with status '#{status}'" if status
  if update_data
    fields = update_data.keys.to_a
    log_message += " and fields: #{fields}"
  end

  $logger.info(log_message)
rescue Aws::DynamoDB::Errors::ServiceError => e
  $logger.error("Failed to update DynamoDB for job=#{job_name}, work=#{work_id}: #{e}")
  raise
end

def process_sqs_messages
  loop do
    # Receive message from SQS queue
    $logger.info('Retrieving messages from SQS queue')
    response = $sqs.receive_message(
      queue_url: SQS_QUEUE_URL,
      attribute_names: ['All'],
      max_number_of_messages: 1,
      message_attribute_names: ['All'],
      visibility_timeout: 600,
      wait_time_seconds: 0
    )
    $logger.info('Retrieved messages from SQS queue')

    # Check if there are any messages
    if response.messages.empty?
      $logger.info('No more messages in the queue.')
      exit
    end

    response.messages.each do |message|
      # Parse the message body
      message_body = JSON.parse(message.body)
      job_name = message_body[JOB_NAME]
      work_id = message_body[WORK_ID]

      # Get work details from DynamoDB instead of SQS message
      work_item = get_work_details(job_name, work_id)

      job_type = work_item[JOB_TYPE]
      context_s3_uri = work_item[CONTEXT_S3_URI]
      image_s3_uris = work_item[IMAGE_S3_URIS]
      original_metadata_s3_uri = work_item[ORIGINAL_METADATA_S3_URI]

      $logger.info("Job name: #{job_name}")
      $logger.info("Work ID: #{work_id}")
      $logger.info("Job type: #{job_type}")
      $logger.info("Context S3 URI: #{context_s3_uri}")
      $logger.info("Image S3 URIs: #{image_s3_uris}")
      $logger.info("Original metadata S3 URI: #{original_metadata_s3_uri}")

      # Update work_status for the item in DynamoDB to "IN PROGRESS"
      update_dynamodb_item(job_name: job_name, work_id: work_id, status: 'IN PROGRESS')

      case job_type
      when 'metadata'
        work_structured_metadata = ImageCaptioningAssistant::Generate::StructuredMetadata.generate_work_structured_metadata(
          image_s3_uris: image_s3_uris,
          context_s3_uri: context_s3_uri,
          llm_kwargs: LLM_KWARGS,
          s3_kwargs: S3_KWARGS,
          resize_kwargs: RESIZE_KWARGS
        )
        work_bias_analysis = ImageCaptioningAssistant::Generate::BiasAnalysis.generate_work_bias_analysis(
          image_s3_uris: image_s3_uris,
          context_s3_uri: context_s3_uri,
          original_metadata_s3_uri: original_metadata_s3_uri,
          llm_kwargs: LLM_KWARGS,
          s3_kwargs: S3_KWARGS,
          resize_kwargs: RESIZE_KWARGS
        )
        # Update DynamoDB with structured metadata and bias analysis fields
        update_data = work_structured_metadata.to_h.merge(work_bias_analysis.to_h)
        update_dynamodb_item(
          job_name: job_name,
          work_id: work_id,
          update_data: update_data,
          status: 'READY FOR REVIEW'
        )
      when 'bias'
        work_bias_analysis = ImageCaptioningAssistant::Generate::BiasAnalysis.generate_work_bias_analysis(
          image_s3_uris: image_s3_uris,
          context_s3_uri: context_s3_uri,
          original_metadata_s3_uri: original_metadata_s3_uri,
          llm_kwargs: LLM_KWARGS,
          s3_kwargs: S3_KWARGS,
          resize_kwargs: RESIZE_KWARGS
        )
        # Update DynamoDB with the bias_analysis field
        update_dynamodb_item(
          job_name: job_name,
          work_id: work_id,
          update_data: work_bias_analysis.to_h,
          status: 'READY FOR REVIEW'
        )
      else
        raise ArgumentError, "#{JOB_TYPE}='#{job_type}' not supported"
      end

      # Delete the message from the queue
      $sqs.delete_message(
        queue_url: SQS_QUEUE_URL,
        receipt_handle: message.receipt_handle
      )
    rescue ImageCaptioningAssistant::Generate::DocumentLengthError => e
      # If it's a document length issue, remove from the queue, we don't intend to handle it
      $logger.warn("Message #{message.message_id} failed with error #{e}")
      $sqs.delete_message(
        queue_url: SQS_QUEUE_URL,
        receipt_handle: message.receipt_handle
      )
    rescue StandardError => e
      $logger.error("Message #{message.message_id} failed with error #{e}")
      $logger.error(e.backtrace.join("\n"))

      # Parse the message body
      message_body = JSON.parse(message.body)
      job_name = message_body[JOB_NAME]
      work_id = message_body[WORK_ID]

      # Update work_status for the item in DynamoDB to "FAILED TO PROCESS"
      update_dynamodb_item(
        job_name: job_name,
        work_id: work_id,
        status: 'FAILED TO PROCESS'
      )
    end
  end
end

# Main execution
process_sqs_messages if __FILE__ == $PROGRAM_NAME
