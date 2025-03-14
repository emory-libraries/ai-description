# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'aws-sdk-dynamodb'

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
JOB_TYPE = 'job_type'
WORK_ID = 'work_id'
WORK_STATUS = 'work_status'

# Initialize AWS clients globally
DYNAMODB = Aws::DynamoDB::Resource.new(region: AWS_REGION)
TABLE = DYNAMODB.table(WORKS_TABLE_NAME)

# Set up logging
LOGGER = Logger.new($stdout)
LOGGER.level = Logger::INFO

# Helper method to handle BigDecimal serialization
def decimal_to_string(obj)
  case obj
  when BigDecimal
    obj.to_s
  when Hash
    obj.transform_values { |v| decimal_to_string(v) }
  when Array
    obj.map { |v| decimal_to_string(v) }
  else
    obj
  end
end

def query_all_items(job_name)
  items = []
  query_params = {
    key_condition_expression: "#{JOB_NAME} = :job_name_val",
    expression_attribute_values: {
      ':job_name_val' => job_name
    },
    projection_expression: "#{WORK_ID}, #{WORK_STATUS}, #{JOB_TYPE}"
  }

  last_evaluated_key = nil

  loop do
    query_params[:exclusive_start_key] = last_evaluated_key if last_evaluated_key

    response = TABLE.query(query_params)
    items.concat(response.items)

    last_evaluated_key = response.last_evaluated_key
    break unless last_evaluated_key
  end

  items
end

def organize_items(items)
  work_ids_by_status = Hash.new { |h, k| h[k] = [] }
  job_types = Set.new

  items.each do |item|
    work_id = item[WORK_ID]
    job_type = item[JOB_TYPE]

    if work_id.nil?
      msg = "Field #{WORK_ID} not found for item."
      LOGGER.warn(msg)
      raise ValueError, msg
    elsif job_type.nil?
      msg = "Field #{JOB_TYPE} not found for #{WORK_ID}=#{work_id}."
      LOGGER.warn(msg)
      raise ValueError, msg
    else
      work_ids_by_status[item[WORK_STATUS]] << work_id
      job_types.add(job_type)
    end
  end

  if job_types.size > 1
    msg = "Multiple job types found for the same job: #{job_types}."
    LOGGER.warn(msg)
    raise ValueError, msg
  end

  [work_ids_by_status, job_types.first]
end

def create_response(status_code, body)
  {
    statusCode: status_code,
    body: JSON.generate(decimal_to_string(body)),
    headers: CORS_HEADERS
  }
end

def handler(event:, context:)
  begin
    query_params = event['queryStringParameters'] || {}

    job_name = query_params[JOB_NAME]

    if job_name.nil?
      return create_response(400, { error: "Missing required query parameter: #{JOB_NAME}" })
    end

    LOGGER.info("Getting progress of job=#{job_name}")
    items = query_all_items(job_name)

    if items.empty?
      return create_response(404, { message: "No data found for #{JOB_NAME}=#{job_name}" })
    end

    work_ids_by_status, job_type = organize_items(items)

    # Return success response
    response = {
      job_progress: work_ids_by_status,
      job_type: job_type
    }

    create_response(200, response)

  rescue Aws::DynamoDB::Errors::ServiceError => e
    LOGGER.error("DynamoDB error: #{e}")
    create_response(500, { error: "Database error", details: e.message })
  rescue StandardError => e
    LOGGER.error("Unexpected error: #{e}")
    create_response(500, { error: "Internal server error" })
  end
end

# Custom error class
class ValueError < StandardError; end
