# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'aws-sdk-bedrockruntime'
require 'json'

module ImageCaptioningAssistant
  module Generate
    module BiasAnalysis
      def self.find_biases_in_short_work(
        image_s3_uris:,
        s3_kwargs:,
        resize_kwargs:,
        llm_kwargs:,
        work_context: nil,
        original_metadata: nil,
        bedrock_runtime: nil
      )
        if bedrock_runtime.nil?
          bedrock_runtime = if llm_kwargs[:region]
                              Aws::BedrockRuntime::Client.new(region: llm_kwargs[:region])
                            else
                              Aws::BedrockRuntime::Client.new
                            end
        end

        raise 'maximum of 2 images (front and back) supported for short work' if image_s3_uris.length > 2

        img_bytes_list = []
        if image_s3_uris.length > 0
          img_bytes_list = BiasAnalysis.load_and_resize_images(
            image_s3_uris: image_s3_uris,
            s3_kwargs: s3_kwargs,
            resize_kwargs: resize_kwargs
          )
        end

        model_name = llm_kwargs[:model_id]
        messages = create_messages(
          img_bytes_list: img_bytes_list,
          work_context: work_context,
          original_metadata: original_metadata,
          model_name: model_name
        )

        court_order = false
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

          if !image_s3_uris.empty? && image_s3_uris.length != json_dict['page_biases'].length
            raise Utils::LLMResponseParsingError, "incorrect number of bias lists for #{image_s3_uris.length} pages"
          end

          if json_dict['metadata_biases'] && json_dict['metadata_biases']['biases']
            json_dict['metadata_biases']['biases'].each do |bias|
              bias['level'] = bias['level'].to_s.downcase if bias['level']
              bias['type'] = bias['type'].to_s.downcase if bias['type']
            end
          end

          json_dict['page_biases'].each do |page|
            next unless page && page['biases']

            page['biases'].each do |bias|
              bias['level'] = bias['level'].to_s.downcase if bias['level']
              bias['type'] = bias['type'].to_s.downcase if bias['type']
            end
          end

          return Data::WorkBiasAnalysis.new(
            metadata_biases: json_dict['metadata_biases'],
            page_biases: json_dict['page_biases']
          )
        rescue StandardError => e
          Utils::LOGGER.warn("Attempt #{attempt + 1}/5 failed: #{e.message}")
          raise e if attempt == 4

          if e.is_a?(Utils::LLMResponseParsingError) || e.is_a?(ArgumentError)
            raw_output = llm_output.to_s.split(Prompts::COT_TAG_END)[-1].to_s.downcase
            court_order = true if raw_output =~ /apologize|i cannot|i can't/
          end
        end

        raise 'Failed to parse model output after 5 attempts'
      end

      def self.create_messages(img_bytes_list:, model_name:, work_context: nil, original_metadata: nil)
        prompt = Prompts::USER_PROMPT_BIAS

        if work_context || original_metadata
          context_str = "Additional Context:\n"
          context_str += "Work Context: #{work_context}\n" if work_context
          context_str += "Original Metadata: #{original_metadata}\n" if original_metadata
          prompt = "#{prompt}\n\n#{context_str}"
        end

        if model_name.include?('claude')
          Utils.format_prompt_for_claude(
            prompt: prompt,
            img_bytes_list: img_bytes_list,
            assistant_start: Prompts::COT_TAG
          )
        elsif model_name.include?('nova')
          Utils.format_prompt_for_nova(
            prompt: prompt,
            img_bytes_list: img_bytes_list,
            assistant_start: Prompts::COT_TAG
          )
        else
          raise ArgumentError, "model #{model_name} not supported"
        end
      end
    end
  end
end
