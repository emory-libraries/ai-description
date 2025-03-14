require 'json'
require 'logger'
require 'aws-sdk-dynamodb'
require 'aws-sdk-s3'
require 'uri'

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
IMAGE_S3_URIS = 'image_s3_uris'
IMAGE_S3_PRESIGNED_URLS = 'image_presigned_urls'

# Initialize AWS clients globally
$dynamodb = Aws::DynamoDB::Resource.new(region: AWS_REGION)
$s3 = Aws::S3::Client.new(region: AWS_REGION)
$table = $dynamodb.table(WORKS_TABLE_NAME)

# Set up logging
$logger = Logger.new($stdout)
$logger.level = Logger::INFO

# Generate presigned URLs from S3 URIs
def generate_presigned_urls(s3_uris)
  presigned_urls = []

  s3_uris.each do |uri|
    parsed_uri = URI.parse(uri)
    bucket_name = parsed_uri.host
    object_key = parsed_uri.path.sub(/^\//, '')

    begin
      presigned_url = $s3.get_object(
        bucket: bucket_name,
        key: object_key,
        expires_in: 60
      ).presigned_url

      presigned_urls << presigned_url
    rescue => e
      $logger.error("Error generating presigned URL for #{uri}: #{e.message}")
      presigned_urls << nil
    end
  end

  presigned_urls
end

# Deserialize DynamoDB data to native Ruby types
def deserialize_dynamodb_item(raw_data)
  if raw_data.is_a?(Array)
    return raw_data.map { |item| deserialize_dynamodb_item(item) }
  end

  return raw_data unless raw_data.is_a?(Hash)

  deserialized_data = {}
  raw_data.each do |key, value|
    if value.is_a?(Hash) && (value.keys & ['S', 'N', 'B', 'M', 'L', 'BOOL', 'NULL', 'SS', 'NS', 'BS']).any?
      deserialized_data[key] = Aws::DynamoDB::Types::AttributeValue.new(value).value
    elsif value.is_a?(Hash)
      deserialized_data[key] = deserialize_dynamodb_item(value)
    else
      deserialized_data[key] = value
    end
  end

  deserialized_data
end

# Create a standardized API response
def create_response(status_code, body)
  {
    statusCode: status_code,
    body: JSON.generate(body),
    headers: CORS_HEADERS
  }
end

def handler(event:, context:)
  begin
    query_params = event['queryStringParameters'] || {}

    job_name = query_params[JOB_NAME]
    unless job_name
      msg = "Missing '#{JOB_NAME}' in query parameters"
      $logger.error(msg)
      return create_response(400, { error: msg })
    end

    work_id = query_params[WORK_ID]
    unless work_id
      msg = "Missing '#{WORK_ID}' in query parameters"
      $logger.error(msg)
      return create_response(400, { error: msg })
    end

    response = $table.get_item(key: { JOB_NAME => job_name, WORK_ID => work_id })
    item = response.item

    if item
      deserialized_item = deserialize_dynamodb_item(item)

      image_s3_uris = deserialized_item[IMAGE_S3_URIS]
      deserialized_item[IMAGE_S3_PRESIGNED_URLS] = generate_presigned_urls(image_s3_uris)

      return create_response(200, { item: deserialized_item })
    else
      $logger.warn("Results not available for #{JOB_NAME}=#{job_name} and #{WORK_ID}=#{work_id}")
      return create_response(404, { error: "Results not available" })
    end
  rescue Aws::DynamoDB::Errors::ServiceError => e
    $logger.error("AWS DynamoDB service error: #{e}")
    create_response(500, { error: "Internal server error" })
  rescue => e
    $logger.error("Unexpected error: #{e}")
    create_response(500, { error: "Internal server error" })
  end
end
