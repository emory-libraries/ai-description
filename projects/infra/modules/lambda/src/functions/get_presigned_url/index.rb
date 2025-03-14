# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'uri'
require 'aws-sdk-s3'
require 'base64'

# Constants
AWS_REGION = ENV['AWS_REGION'] || 'us-east-1'
CORS_HEADERS = {
  'Access-Control-Allow-Origin' => '*',
  'Access-Control-Allow-Headers' => '*',
  'Access-Control-Allow-Methods' => '*',
  'Access-Control-Allow-Credentials' => true
}
S3_URI = 's3_uri'
EXPIRES_IN = 'expires_in'
DEFAULT_EXPIRATION = 3600 # Default expiration time (in seconds)

# Set up logging
logger = Logger.new($stdout)
logger.level = Logger::INFO

# Initialize AWS client globally
Aws::S3::Client.new(region: AWS_REGION)

def create_response(status_code, body)
  {
    statusCode: status_code,
    body: JSON.generate(body),
    headers: CORS_HEADERS
  }
end

def generate_presigned_url(s3_uri, expiration = DEFAULT_EXPIRATION)
  parsed_uri = URI.parse(s3_uri)

  # Validate S3 URI format
  raise "Invalid S3 URI scheme: #{parsed_uri.scheme}. Expected 's3'" if parsed_uri.scheme != 's3'

  bucket_name = parsed_uri.host
  object_key = parsed_uri.path.sub(%r{^/}, '')

  raise 'S3 URI must contain both bucket name and object key' if bucket_name.nil? || object_key.empty?

  begin
    signer = Aws::S3::Presigner.new(client: s3)
    signer.presigned_url(
      :get_object,
      bucket: bucket_name,
      key: object_key,
      expires_in: expiration
    )
  rescue StandardError => e
    logger.error("Error generating presigned URL: #{e}")
    raise
  end
end

def handler(event:, context:)
  # Extract parameters based on event source
  if event['queryStringParameters']
    # API Gateway invocation
    s3_uri = event['queryStringParameters'][S3_URI]
    expires_in_str = event['queryStringParameters'][EXPIRES_IN] || DEFAULT_EXPIRATION.to_s
  else
    # Direct Lambda invocation
    s3_uri = event[S3_URI]
    expires_in_str = (event[EXPIRES_IN] || DEFAULT_EXPIRATION).to_s
  end

  # Validate required parameters
  if s3_uri.nil? || s3_uri.empty?
    logger.error('No S3 URI provided')
    return create_response(400, { 'error' => "Missing required parameter 's3_uri'" })
  end

  # Parse expiration time
  begin
    expires_in = expires_in_str.to_i
    expires_in = DEFAULT_EXPIRATION if expires_in <= 0
  rescue StandardError
    expires_in = DEFAULT_EXPIRATION
  end

  # Generate the presigned URL
  presigned_url = generate_presigned_url(s3_uri, expires_in)

  # Return success response
  create_response(
    200,
    {
      'presigned_url' => presigned_url,
      's3_uri' => s3_uri,
      'expires_in_seconds' => expires_in
    }
  )
rescue URI::InvalidURIError, ArgumentError => e
  logger.error("Validation error: #{e}")
  create_response(400, { 'error' => e.message })
rescue Aws::S3::Errors::ServiceError => e
  logger.error("AWS service error: #{e}")
  create_response(500, { 'error' => 'Error accessing S3 resource' })
rescue StandardError => e
  logger.error("Unexpected error: #{e}")
  create_response(500, { 'error' => 'Internal server error' })
end
