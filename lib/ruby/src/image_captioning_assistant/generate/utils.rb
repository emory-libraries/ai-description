# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'base64'
require 'json'
require 'logger'
require 'mini_magick'
require 'stringio'

module ImageCaptioningAssistant
  module Generate
    module Utils
      LOGGER = Logger.new($stdout)
      LOGGER.level = Logger::INFO

      class LLMResponseParsingError < StandardError; end

      def self.convert_bytes_to_base64_str(img_bytes)
        Base64.strict_encode64(img_bytes)
      end

      def self.convert_and_reduce_image(image_bytes:, max_dimension: 2048, jpeg_quality: 95)
        image = MiniMagick::Image.read(image_bytes)
        image.format "jpg"
        image.resize "#{max_dimension}x#{max_dimension}>"
        image.quality jpeg_quality
        image.to_blob
      end

      def self.load_and_resize_images(image_s3_uris, s3_kwargs, resize_kwargs)
        resized_img_bytes_list = []
        
        image_s3_uris.each do |image_s3_uri|
          bucket, key = AWS::S3.parse_s3_uri(image_s3_uri)
          img_bytes = AWS::S3.load_to_bytes(
            s3_bucket: bucket,
            s3_key: key,
            s3_client_kwargs: s3_kwargs
          )
          
          resized_img_bytes = convert_and_reduce_image(
            image_bytes: img_bytes,
            max_dimension: resize_kwargs[:max_dimension] || 2048,
            jpeg_quality: resize_kwargs[:jpeg_quality] || 95
          )
          
          resized_img_bytes_list << resized_img_bytes
        end
        
        resized_img_bytes_list
      end

      def self.format_prompt_for_claude(prompt:, img_bytes_list:, assistant_start:)
        content = [{"type" => "text", "text" => prompt}]
        
        img_bytes_list.each do |img_bytes|
          img_message = {
            "type" => "image",
            "source" => {
              "type" => "base64",
              "media_type" => "image/jpeg",
              "data" => convert_bytes_to_base64_str(img_bytes)
            }
          }
          content << img_message
        end
        
        msg_list = [{"role" => "user", "content" => content}]
        
        if assistant_start
          msg_list << {"role" => "assistant", "content" => assistant_start}
        end
        
        msg_list
      end

      def self.format_prompt_for_nova(prompt:, img_bytes_list:, assistant_start:)
        content = [{"text" => prompt}]
        
        img_bytes_list.each do |img_bytes|
          img_message = {
            "image" => {
              "format" => "jpeg",
              "source" => {
                "bytes" => convert_bytes_to_base64_str(img_bytes)
              }
            }
          }
          content << img_message
        end
        
        msg_list = [{"role" => "user", "content" => content}]
        
        if assistant_start
          msg_list << {"role" => "assistant", "content" => assistant_start}
        end
        
        msg_list
      end

      def self.format_request_body(model_name, messages, court_order: false)
        if model_name.include?('claude')
          request_body = {
            "anthropic_version" => "bedrock-2023-05-31",
            "max_tokens" => 4096,
            "temperature" => 0.2,
            "system" => court_order ? Prompts::SYSTEM_PROMPT_COURT_ORDER : Prompts::SYSTEM_PROMPT
          }
          
          request_body["messages"] = messages
          
          request_body
        elsif model_name.include?('nova')
          if court_order
            messages[0]["content"][0]["text"] = Prompts::SYSTEM_PROMPT_COURT_ORDER
          end
          
          {
            "messages" => messages,
            "max_tokens" => 4096,
            "temperature" => 0.2
          }
        else
          raise ArgumentError, "Unsupported model: #{model_name}"
        end
      end

      def self.extract_json_and_cot_from_text(text)
        parts = text.split(Prompts::COT_TAG_END)
        if parts.length < 2
          LOGGER.error("Could not find COT_TAG_END in response: #{text}")
          raise LLMResponseParsingError, "No COT_TAG_END found in response"
        end
        
        cot = parts[0].sub(Prompts::COT_TAG, "").strip
        json_text = parts[1].strip
        
        begin
          json_dict = JSON.parse(json_text)
          return [cot, json_dict]
        rescue JSON::ParserError
          json_pattern = /```(?:json)?\s*(.*?)\s*```/m
          json_match = json_text.match(json_pattern)
          
          if json_match
            begin
              json_dict = JSON.parse(json_match[1].strip)
              return [cot, json_dict]
            rescue JSON::ParserError => e
              LOGGER.error("Failed to parse JSON from code block: #{e.message}")
              LOGGER.error("JSON content: #{json_match[1].strip}")
              raise LLMResponseParsingError, "Failed to parse JSON from code block: #{e.message}"
            end
          else
            LOGGER.error("No JSON found in response")
            LOGGER.error("Response text: #{json_text}")
            raise LLMResponseParsingError, "No JSON found in response"
          end
        end
      end
    end
  end
end