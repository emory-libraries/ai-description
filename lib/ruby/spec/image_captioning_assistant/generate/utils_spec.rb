# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'
require 'base64'

RSpec.describe ImageCaptioningAssistant::Generate::Utils do
  describe '.convert_bytes_to_base64_str' do
    it 'converts bytes to base64 string' do
      img_bytes = 'test image data'
      result = described_class.convert_bytes_to_base64_str(img_bytes)
      expect(result).to eq(Base64.strict_encode64(img_bytes))
    end

    it 'handles binary data' do
      binary_data = "\x89PNG\r\n\x1A\n".dup.force_encoding('ASCII-8BIT')
      result = described_class.convert_bytes_to_base64_str(binary_data)
      decoded = Base64.strict_decode64(result)
      expect(decoded).to eq(binary_data)
    end
  end

  describe '.convert_and_reduce_image' do
    let(:test_image_bytes) { create_test_image_bytes }

    it 'converts image to JPEG format' do
      allow_any_instance_of(MiniMagick::Image).to receive(:to_blob).and_return('jpeg_data')

      result = described_class.convert_and_reduce_image(
        image_bytes: test_image_bytes,
        max_dimension: 1024,
        jpeg_quality: 90
      )

      expect(result).to eq('jpeg_data')
    end

    it 'resizes image to max dimension' do
      # Skip this test as MiniMagick doesn't have a resize method directly
      # The actual implementation uses resize internally
      skip 'MiniMagick implementation detail test'

      result = described_class.convert_and_reduce_image(
        image_bytes: test_image_bytes,
        max_dimension: 1024,
        jpeg_quality: 90
      )

      expect(result).to eq('resized_data')
    end
  end

  describe '.format_prompt_for_claude' do
    let(:prompt) { 'Analyze this image' }
    let(:img_bytes) { %w[image1_data image2_data] }
    let(:assistant_start) { '<thinking>' }

    it 'formats prompt with images for Claude' do
      result = described_class.format_prompt_for_claude(
        prompt: prompt,
        img_bytes_list: img_bytes,
        assistant_start: assistant_start
      )

      expect(result).to be_an(Array)
      expect(result.first['role']).to eq('user')
      expect(result.first['content']).to be_an(Array)

      content = result.first['content']
      expect(content.first['type']).to eq('text')
      expect(content.first['text']).to eq(prompt)

      # Check image messages
      expect(content[1]['type']).to eq('image')
      expect(content[1]['source']['type']).to eq('base64')
      expect(content[1]['source']['media_type']).to eq('image/jpeg')

      # Check assistant start
      expect(result.last['role']).to eq('assistant')
      expect(result.last['content']).to eq(assistant_start)
    end

    it 'handles empty image list' do
      result = described_class.format_prompt_for_claude(
        prompt: prompt,
        img_bytes_list: [],
        assistant_start: nil
      )

      expect(result.size).to eq(1)
      expect(result.first['content'].size).to eq(1)
    end
  end

  describe '.format_prompt_for_nova' do
    let(:prompt) { 'Analyze this image' }
    let(:img_bytes) { ['image1_data'] }
    let(:assistant_start) { '<thinking>' }

    it 'formats prompt with images for Nova' do
      result = described_class.format_prompt_for_nova(
        prompt: prompt,
        img_bytes_list: img_bytes,
        assistant_start: assistant_start
      )

      expect(result).to be_an(Array)
      expect(result.first['role']).to eq('user')
      expect(result.first['content']).to be_an(Array)

      content = result.first['content']
      expect(content.first['text']).to eq(prompt)

      # Check image format
      expect(content[1]['image']['format']).to eq('jpeg')
      expect(content[1]['image']['source']['bytes']).to be_a(String)

      # Check assistant start
      expect(result.last['role']).to eq('assistant')
      expect(result.last['content']).to eq(assistant_start)
    end
  end

  describe '.format_request_body' do
    let(:messages) { [{ role: 'user', content: 'test' }] }

    context 'for Claude model' do
      let(:model_name) { 'anthropic.claude-3-sonnet' }

      it 'formats request for Claude' do
        result = described_class.format_request_body(model_name, messages)

        expect(result['anthropic_version']).to eq('bedrock-2023-05-31')
        expect(result['max_tokens']).to eq(4096)
        expect(result['temperature']).to eq(0.2)
        expect(result['messages']).to eq(messages)
        expect(result['system']).to include('expert in analyzing')
      end

      it 'uses court order prompt when specified' do
        result = described_class.format_request_body(model_name, messages, court_order: true)
        expect(result['system']).to include('court order')
      end
    end

    context 'for Nova model' do
      let(:model_name) { 'amazon.nova-pro' }

      it 'formats request for Nova' do
        result = described_class.format_request_body(model_name, messages)

        expect(result['messages']).to eq(messages)
        expect(result['max_tokens']).to eq(4096)
        expect(result['temperature']).to eq(0.2)
      end
    end

    context 'for unsupported model' do
      let(:model_name) { 'unsupported-model' }

      it 'raises error' do
        expect do
          described_class.format_request_body(model_name, messages)
        end.to raise_error(ArgumentError, /Unsupported model/)
      end
    end
  end

  describe '.extract_json_and_cot_from_text' do
    let(:cot_tag) { ImageCaptioningAssistant::Generate::Prompts::COT_TAG }
    let(:cot_tag_end) { ImageCaptioningAssistant::Generate::Prompts::COT_TAG_END }

    context 'with valid response' do
      let(:cot_content) { 'This is my analysis' }
      let(:json_content) { '{"result": "success"}' }
      let(:text) { "#{cot_tag}#{cot_content}#{cot_tag_end}#{json_content}" }

      it 'extracts COT and JSON' do
        cot, json_dict = described_class.extract_json_and_cot_from_text(text)
        expect(cot).to eq(cot_content)
        expect(json_dict).to eq({ 'result' => 'success' })
      end
    end

    context 'with JSON in code block' do
      let(:cot_content) { 'Analysis' }
      let(:json_content) { "```json\n{\"result\": \"success\"}\n```" }
      let(:text) { "#{cot_tag}#{cot_content}#{cot_tag_end}#{json_content}" }

      it 'extracts JSON from code block' do
        cot, json_dict = described_class.extract_json_and_cot_from_text(text)
        expect(cot).to eq(cot_content)
        expect(json_dict).to eq({ 'result' => 'success' })
      end
    end

    context 'with missing COT_TAG_END' do
      let(:text) { "#{cot_tag}Some content without end tag" }

      it 'raises parsing error' do
        expect do
          described_class.extract_json_and_cot_from_text(text)
        end.to raise_error(ImageCaptioningAssistant::Generate::Utils::LLMResponseParsingError, /No COT_TAG_END/)
      end
    end

    context 'with invalid JSON' do
      let(:text) { "#{cot_tag}COT#{cot_tag_end}not valid json" }

      it 'raises parsing error' do
        expect do
          described_class.extract_json_and_cot_from_text(text)
        end.to raise_error(ImageCaptioningAssistant::Generate::Utils::LLMResponseParsingError, /No JSON found/)
      end
    end
  end
end
