# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'aws-sdk-dynamodb'
require 'bigdecimal'

# Constants
AWS_REGION = ENV['AWS_REGION']
WORKS_TABLE_NAME = ENV['WORKS_TABLE_NAME']
CORS_HEADERS = {
  'Access-Control-Allow-Origin' => '*',
  'Access-Control-Allow-Headers' => '*',
  'Access-Control-Allow-Methods' => '*',
  'Access-Control-Allow-Credentials' => true
}
JOB_NAME = 'job_name'
WORK_ID = 'work_id'
UPDATED_FIELDS = 'updated_fields'

# Initialize AWS clients globally
DYNAMODB = Aws::DynamoDB::Resource.new(region: AWS_REGION)
TABLE = DYNAMODB.table(WORKS_TABLE_NAME)

# Set up logging
LOGGER = Logger.new($stdout)
LOGGER.level = Logger::INFO

# Custom JSON encoder for BigDecimal
class DecimalSerializer
  def self.dump(obj)
    case obj
    when BigDecimal
      obj.to_s
    when Hash
      obj.transform_values { |v| dump(v) }
    when Array
      obj.map { |v| dump(v) }
    else
      obj
    end
  end
end

def create_response(status_code, body)
  {
    statusCode: status_code,
    body: JSON.generate(DecimalSerializer.dump(body)),
    headers: CORS_HEADERS
  }
end

def handler(event:, context:)
  begin
    # Parse the request body
    body = JSON.parse(event['body'])
    job_name = body[JOB_NAME]
    work_id = body[WORK_ID]
    updated_fields = body[UPDATED_FIELDS]

    if job_name.nil?
      msg = "Missing required parameter '#{JOB_NAME}'"
      LOGGER.error(msg)
      return create_response(400, { error: msg })
    end
    if work_id.nil?
      msg = "Missing required parameter '#{WORK_ID}'"
      LOGGER.error(msg)
      return create_response(400, { error: msg })
    end
    if updated_fields.nil?
      msg = "Missing required parameter '#{UPDATED_FIELDS}'"
      LOGGER.error(msg)
      return create_response(400, { error: msg })
    end

    # Prepare the update expression and attribute values
    update_expression = 'SET '
    expression_attribute_values = {}
    expression_attribute_names = {}

    updated_fields.each do |key, value|
      update_expression += "##{key} = :#{key}, "
      expression_attribute_values[":#{key}"] = value
      expression_attribute_names["##{key}"] = key
    end

    # Remove the trailing comma and space
    update_expression = update_expression[0...-2]

    # Update the item in DynamoDB
    response = TABLE.update_item({
      key: { JOB_NAME => job_name, WORK_ID => work_id },
      update_expression: update_expression,
      expression_attribute_values: expression_attribute_values,
      expression_attribute_names: expression_attribute_names,
      return_values: 'ALL_NEW'
    })

    updated_item = response.attributes
    if updated_item
      LOGGER.info("Successfully updated item for #{JOB_NAME}=#{job_name} and #{WORK_ID}=#{work_id}")
      create_response(200, { message: 'Item updated successfully', item: updated_item })
    else
      LOGGER.warn("No item found for #{JOB_NAME}=#{job_name} and #{WORK_ID}=#{work_id}")
      create_response(404, { error: 'Item not found' })
    end

  rescue Aws::DynamoDB::Errors::ServiceError => e
    LOGGER.error("AWS service error: #{e}")
    create_response(500, { error: 'Internal server error' })
  rescue JSON::ParserError
    LOGGER.error('Invalid JSON in request body')
    create_response(400, { error: 'Invalid JSON in request body' })
  rescue StandardError => e
    LOGGER.error("Unexpected error: #{e}")
    create_response(500, { error: 'Internal server error' })
  end
end