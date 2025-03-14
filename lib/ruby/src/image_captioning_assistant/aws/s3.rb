# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'aws-sdk-s3'
require 'uri'

module ImageCaptioningAssistant
  module AWS
    # S3 utility functions
    module S3
      # Parse S3 URI into bucket and key
      def self.parse_s3_uri(s3_uri)
        return [nil, nil] if s3_uri.nil? || s3_uri.empty?

        # Add logging
        puts "Parsing S3 URI: #{s3_uri}"

        # Handle s3://bucket-name/key format
        if s3_uri.start_with?('s3://')
          uri = URI.parse(s3_uri)
          bucket = uri.host
          key = uri.path.sub(%r{^/}, '')
          puts "Parsed s3:// URI - bucket: #{bucket}, key: #{key}"
          return [bucket, key]
        end

        # Handle bucket-name/key format or just the key if bucket is known
        if s3_uri.include?('/')
          parts = s3_uri.split('/', 2)
          puts "Parsed bucket/key format - bucket: #{parts[0]}, key: #{parts[1]}"
          [parts[0], parts[1]]
        else
          # If it's just a key, use the UPLOADS_BUCKET_NAME from environment
          bucket = ENV['UPLOADS_BUCKET_NAME']
          puts "Using uploads bucket - bucket: #{bucket}, key: #{s3_uri}"
          raise ArgumentError, 'S3 key must not be blank' if s3_uri.strip.empty?

          [bucket, s3_uri]
        end
      end

      # Load S3 object to string
      def self.load_to_str(s3_bucket:, s3_key:, s3_client_kwargs: {})
        raise ArgumentError, 'S3 bucket must not be blank' if s3_bucket.nil? || s3_bucket.strip.empty?
        raise ArgumentError, 'S3 key must not be blank' if s3_key.nil? || s3_key.strip.empty?

        puts "Loading S3 object as string - bucket: #{s3_bucket}, key: #{s3_key}"
        s3_client = Aws::S3::Client.new(**s3_client_kwargs)
        response = s3_client.get_object(bucket: s3_bucket, key: s3_key)
        response.body.read
      end

      # Load S3 object to binary
      def self.load_to_bytes(s3_bucket:, s3_key:, s3_client_kwargs: {})
        raise ArgumentError, 'S3 bucket must not be blank' if s3_bucket.nil? || s3_bucket.strip.empty?
        raise ArgumentError, 'S3 key must not be blank' if s3_key.nil? || s3_key.strip.empty?

        puts "Loading S3 object as bytes - bucket: #{s3_bucket}, key: #{s3_key}"
        s3_client = Aws::S3::Client.new(**s3_client_kwargs)
        response = s3_client.get_object(bucket: s3_bucket, key: s3_key)
        response.body.read
      end
    end
  end
end
