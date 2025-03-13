# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'logger'

module ImageCaptioningAssistant
  module Generate
    module BiasAnalysis
      LOGGER = Logger.new($stdout)
      LOGGER.level = Logger::INFO

      def self.generate_work_bias_analysis(
        image_s3_uris:,
        llm_kwargs:,
        s3_kwargs:,
        resize_kwargs:,
        context_s3_uri: nil,
        original_metadata_s3_uri: nil
      )
        llm_kwargs[:model_id] ||= "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        original_metadata = nil
        if original_metadata_s3_uri && !original_metadata_s3_uri.to_s.empty?
          bucket, key = AWS::S3.parse_s3_uri(original_metadata_s3_uri)
          original_metadata = AWS::S3.load_to_str(
            s3_bucket: bucket,
            s3_key: key,
            s3_client_kwargs: s3_kwargs
          )
        end

        work_context = nil
        if context_s3_uri && !context_s3_uri.to_s.empty?
          bucket, key = AWS::S3.parse_s3_uri(context_s3_uri)
          work_context = AWS::S3.load_to_str(
            s3_bucket: bucket,
            s3_key: key,
            s3_client_kwargs: s3_kwargs
          )
        end

        if image_s3_uris.length <= 2
          find_biases_in_short_work(
            image_s3_uris: image_s3_uris,
            s3_kwargs: s3_kwargs,
            resize_kwargs: resize_kwargs,
            llm_kwargs: llm_kwargs,
            work_context: work_context,
            original_metadata: original_metadata
          )
        else
          find_biases_in_long_work(
            image_s3_uris: image_s3_uris,
            llm_kwargs: llm_kwargs,
            s3_kwargs: s3_kwargs,
            original_metadata: original_metadata,
            work_context: work_context,
            resize_kwargs: resize_kwargs
          )
        end
      end
    end
  end
end