# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'aws-sdk-bedrockruntime'
require 'json'
require 'logger'

module ImageCaptioningAssistant
  module Generate
    module BiasAnalysis
      LOGGER = Logger.new($stdout)
      LOGGER.level = Logger::INFO

      def self.find_biases_in_original_metadata(
        original_metadata:,
        bedrock_runtime:,
        llm_kwargs:,
        work_context: nil
      )
        LOGGER.info('Analyzing original metadata')
        llm_output = find_biases_in_short_work(
          image_s3_uris: [],
          s3_kwargs: {},
          llm_kwargs: llm_kwargs,
          resize_kwargs: {},
          work_context: work_context,
          original_metadata: original_metadata,
          bedrock_runtime: bedrock_runtime
        )
        llm_output.metadata_biases
      end

      def self.find_biases_in_images(
        image_s3_uris:,
        s3_kwargs:,
        resize_kwargs:,
        bedrock_runtime:,
        llm_kwargs:,
        work_context: nil
      )
        LOGGER.info("Analyzing #{image_s3_uris.length} images")
        page_biases = []

        image_s3_uris.each do |image_s3_uri|
          LOGGER.debug("Analyzing image #{image_s3_uri}")
          llm_output = find_biases_in_short_work(
            image_s3_uris: [image_s3_uri],
            s3_kwargs: s3_kwargs,
            llm_kwargs: llm_kwargs,
            resize_kwargs: resize_kwargs,
            work_context: work_context,
            bedrock_runtime: bedrock_runtime
          )
          page_biases << llm_output.page_biases[0]
        end

        page_biases
      end

      def self.find_biases_in_long_work(
        image_s3_uris:,
        llm_kwargs:,
        s3_kwargs:,
        resize_kwargs:,
        original_metadata: nil,
        work_context: nil
      )
        bedrock_runtime = if llm_kwargs[:region]
                            Aws::BedrockRuntime::Client.new(region: llm_kwargs[:region])
                          else
                            Aws::BedrockRuntime::Client.new
                          end

        metadata_biases = Data::Biases.new(biases: [])
        if original_metadata
          metadata_biases = find_biases_in_original_metadata(
            original_metadata: original_metadata,
            work_context: work_context,
            bedrock_runtime: bedrock_runtime,
            llm_kwargs: llm_kwargs
          )
        end

        page_biases = find_biases_in_images(
          image_s3_uris: image_s3_uris,
          bedrock_runtime: bedrock_runtime,
          llm_kwargs: llm_kwargs,
          resize_kwargs: resize_kwargs,
          s3_kwargs: s3_kwargs,
          work_context: work_context
        )

        begin
          Data::WorkBiasAnalysis.new(
            metadata_biases: metadata_biases,
            page_biases: page_biases
          )
        rescue StandardError => e
          LOGGER.warn('Failed to cast metadata biases and page biases into WorkBiasAnalysis, debug to log full output')
          LOGGER.debug("metadata_biases:\n #{metadata_biases.inspect} \n\n\n")
          LOGGER.debug("page_biases:\n #{page_biases.inspect} \n\n\n")
          raise e
        end
      end
    end
  end
end
