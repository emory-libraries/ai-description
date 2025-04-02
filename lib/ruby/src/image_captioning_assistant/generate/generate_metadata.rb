# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'aws-sdk-bedrockruntime'
require 'json'

module ImageCaptioningAssistant
  module Generate
    class DocumentLengthError < StandardError
      attr_reader :error_code

      def initialize(message, error_code = nil)
        @error_code = error_code
        super(message)
      end

      def to_s
        "DocumentLengthError: #{@message} (Error Code: #{error_code})"
      end
    end

    module Metadata
      def self.generate_metadata_from_images(img_bytes_list:, llm_kwargs:, work_context: nil)
        bedrock_runtime = if llm_kwargs[:region]
                            Aws::BedrockRuntime::Client.new(region: llm_kwargs[:region])
                          else
                            Aws::BedrockRuntime::Client.new
                          end

        text_prompt = "#{Prompts::USER_PROMPT_METADATA}\nContextual Help: #{work_context}"
        model_name = llm_kwargs[:model_id]
        court_order = false

        messages = if model_name.include?('claude')
                     Utils.format_prompt_for_claude(
                       prompt: text_prompt,
                       img_bytes_list: img_bytes_list,
                       assistant_start: Prompts::COT_TAG
                     )
                   elsif model_name.include?('nova')
                     Utils.format_prompt_for_nova(
                       prompt: text_prompt,
                       img_bytes_list: img_bytes_list,
                       assistant_start: Prompts::COT_TAG
                     )
                   else
                     raise ArgumentError, "model #{model_name} not supported"
                   end

        llm_output = nil
        5.times do |attempt|
          request_body = Utils.format_request_body(model_name, messages, court_order: court_order)

          response = bedrock_runtime.invoke_model({
                                                    model_id: model_name,
                                                    body: JSON.generate(request_body)
                                                  })

          result = JSON.parse(response.body.read)
          llm_output = if model_name.include?('claude')
                         result['content'][0]['text']
                       elsif model_name.include?('nova')
                         result['output']['message']['content'][0]['text']
                       else
                         raise ArgumentError, "ModelId #{model_name} not supported"
                       end

          cot, json_dict = Utils.extract_json_and_cot_from_text(llm_output)
          Utils::LOGGER.debug("\n\n********** CHAIN OF THOUGHT **********\n #{cot} \n\n")

          unless json_dict['metadata'].is_a?(Hash)
            raise Utils::LLMResponseParsingError, 'Invalid metadata format in response'
          end

          metadata = {}

          # Convert string keys to symbols for all explained values
          metadata[:description] = convert_to_explained_value_hash(json_dict['metadata']['description'])

          transcription_data = json_dict['metadata']['transcription']
          metadata[:transcription] = if transcription_data.is_a?(Hash) && transcription_data.key?('transcriptions')
                                       {
                                         transcriptions: transcription_data['transcriptions'].map do |t|
                                           {
                                             printed_text: t['printed_text'] || [],
                                             handwriting: t['handwriting'] || []
                                           }
                                         end,
                                         model_notes: transcription_data['model_notes'] || ''
                                       }
                                     elsif transcription_data.is_a?(Array)
                                       {
                                         transcriptions: transcription_data.map do |t|
                                           {
                                             printed_text: t['printed_text'] || [],
                                             handwriting: t['handwriting'] || []
                                           }
                                         end,
                                         model_notes: ''
                                       }
                                     else
                                       {
                                         transcriptions: [
                                           { printed_text: [], handwriting: [] }
                                         ],
                                         model_notes: ''
                                       }
                                     end

          metadata[:date] = convert_to_explained_value_hash(json_dict['metadata']['date'])
          metadata[:location] = convert_to_explained_value_hash(json_dict['metadata']['location'])
          metadata[:publication_info] = convert_to_explained_value_hash(json_dict['metadata']['publication_info'])
          metadata[:contextual_info] = convert_to_explained_value_hash(json_dict['metadata']['contextual_info'])

          format_value = json_dict['metadata']['format']
          if format_value.is_a?(Hash) && Data::Constants::LibraryFormat.all.include?(format_value['value'])
            metadata[:format] = convert_to_explained_value_hash(format_value)
          else
            default_format = 'Still Image'
            metadata[:format] = {
              value: default_format,
              explanation: format_value.is_a?(Hash) ? format_value['explanation'] : 'Generated from image analysis'
            }
          end

          metadata[:genre] = convert_to_explained_value_hash(json_dict['metadata']['genre'])
          metadata[:objects] = convert_to_explained_value_hash(json_dict['metadata']['objects'])
          metadata[:actions] = convert_to_explained_value_hash(json_dict['metadata']['actions'])
          metadata[:people] = convert_to_explained_value_hash(json_dict['metadata']['people'])
          metadata[:topics] = convert_to_explained_value_hash(json_dict['metadata']['topics'])

          return Data::Metadata.new(metadata)
        rescue StandardError => e
          Utils::LOGGER.warn("Attempt #{attempt + 1}/5 failed: #{e.message}")
          raise e if attempt == 4

          if e.is_a?(Utils::LLMResponseParsingError)
            raw_output = llm_output.to_s.split(Prompts::COT_TAG_END)[-1].to_s.downcase
            court_order = true if raw_output =~ /apologize|i cannot|i can't/
          end
        end

        raise 'Failed to parse model output after 5 attempts'
      end

      # Helper method to convert string keys to symbol keys for ExplainedValue
      def self.convert_to_explained_value_hash(hash_data)
        if hash_data.is_a?(Hash) && hash_data['value'] && hash_data['explanation']
          {
            value: hash_data['value'],
            explanation: hash_data['explanation']
          }
        else
          # Fallback for missing or malformed data
          {
            value: hash_data.is_a?(Hash) ? (hash_data['value'] || '') : (hash_data || ''),
            explanation: 'Generated from image analysis'
          }
        end
      end

      def self.generate_metadata_from_s3_images(image_s3_uris:, llm_kwargs:, s3_kwargs:, resize_kwargs:, context_s3_uri: nil)
        if image_s3_uris.length > 2
          msg = "Structured metadata only supports documents of 1-2 pages, #{image_s3_uris.length} pages provided."
          Utils::LOGGER.warn(msg)
          raise DocumentLengthError.new(msg)
        end

        llm_kwargs[:model_id] ||= 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

        work_context = nil
        if context_s3_uri && !context_s3_uri.to_s.empty?
          bucket, key = AWS::S3.parse_s3_uri(context_s3_uri)
          work_context = AWS::S3.load_to_str(
            s3_bucket: bucket,
            s3_key: key,
            s3_client_kwargs: s3_kwargs
          )
        end

        img_bytes_list = Utils.load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)

        generate_metadata_from_images(
          img_bytes_list: img_bytes_list,
          llm_kwargs: llm_kwargs,
          work_context: work_context
        )
      end
    end
  end
end
