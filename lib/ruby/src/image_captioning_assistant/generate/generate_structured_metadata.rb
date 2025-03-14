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
        "DocumentLengthError: #{message} (Error Code: #{error_code})"
      end
    end

    module StructuredMetadata
      def self.generate_structured_metadata(img_bytes_list:, llm_kwargs:, work_context: nil)
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

          metadata[:description] =
            { value: json_dict['metadata']['description'], explanation: 'Generated from image analysis' }

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

          metadata[:date] = { value: json_dict['metadata']['date'], explanation: 'Generated from image analysis' }
          metadata[:location] =
            { value: json_dict['metadata']['location'] || [], explanation: 'Generated from image analysis' }
          metadata[:publication_info] =
            { value: json_dict['metadata']['publication_info'] || '', explanation: 'Generated from image analysis' }
          metadata[:contextual_info] =
            { value: json_dict['metadata']['contextual_info'] || '', explanation: 'Generated from image analysis' }

          format_value = json_dict['metadata']['format']
          format_value = 'Still Image' unless Data::Constants::LibraryFormat.all.include?(format_value)
          metadata[:format] = { value: format_value, explanation: 'Generated from image analysis' }

          metadata[:genre] =
            { value: json_dict['metadata']['genre'] || [], explanation: 'Generated from image analysis' }
          metadata[:objects] =
            { value: json_dict['metadata']['objects'] || [], explanation: 'Generated from image analysis' }
          metadata[:actions] =
            { value: json_dict['metadata']['actions'] || [], explanation: 'Generated from image analysis' }
          metadata[:people] =
            { value: json_dict['metadata']['people'] || [], explanation: 'Generated from image analysis' }
          metadata[:topics] =
            { value: json_dict['metadata']['topics'] || [], explanation: 'Generated from image analysis' }

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

      def self.generate_work_structured_metadata(image_s3_uris:, llm_kwargs:, s3_kwargs:, resize_kwargs:, context_s3_uri: nil)
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

        generate_structured_metadata(
          img_bytes_list: img_bytes_list,
          llm_kwargs: llm_kwargs,
          work_context: work_context
        )
      end
    end
  end
end
