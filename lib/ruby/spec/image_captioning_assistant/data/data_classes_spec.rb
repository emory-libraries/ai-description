# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'

RSpec.describe ImageCaptioningAssistant::Data do
  describe 'ExplainedValue' do
    subject(:explained_value_class) { described_class::ExplainedValue }

    context 'with valid attributes' do
      let(:explained_value) { explained_value_class.new(value: 'test', explanation: 'test explanation') }

      it 'creates instance with value and explanation' do
        expect(explained_value.value).to eq('test')
        expect(explained_value.explanation).to eq('test explanation')
      end

      it 'converts to hash' do
        expect(explained_value.to_h).to eq({
          value: 'test',
          explanation: 'test explanation'
        })
      end
    end

    context 'with invalid attributes' do
      it 'raises error for nil value' do
        expect do
          explained_value_class.new(value: nil, explanation: 'test')
        end.to raise_error(ArgumentError, 'Value cannot be nil')
      end

      it 'raises error for nil explanation' do
        expect do
          explained_value_class.new(value: 'test', explanation: nil)
        end.to raise_error(ArgumentError, 'Explanation is required')
      end

      it 'raises error for empty explanation' do
        expect do
          explained_value_class.new(value: 'test', explanation: '')
        end.to raise_error(ArgumentError, 'Explanation is required')
      end
    end
  end

  describe 'PageTranscription' do
    subject(:page_transcription_class) { described_class::PageTranscription }

    context 'with valid attributes' do
      let(:transcription) do
        page_transcription_class.new(
          printed_text: ['Line 1', 'Line 2'],
          handwriting: ['Note 1']
        )
      end

      it 'creates instance with text arrays' do
        expect(transcription.printed_text).to eq(['Line 1', 'Line 2'])
        expect(transcription.handwriting).to eq(['Note 1'])
      end

      it 'accepts empty arrays' do
        empty_transcription = page_transcription_class.new
        expect(empty_transcription.printed_text).to eq([])
        expect(empty_transcription.handwriting).to eq([])
      end

      it 'converts to hash' do
        expect(transcription.to_h).to eq({
          printed_text: ['Line 1', 'Line 2'],
          handwriting: ['Note 1']
        })
      end
    end

    context 'with invalid attributes' do
      it 'raises error for non-array printed_text' do
        expect do
          page_transcription_class.new(printed_text: 'not an array')
        end.to raise_error(ArgumentError, 'printed_text must be an array')
      end

      it 'raises error for non-array handwriting' do
        expect do
          page_transcription_class.new(handwriting: 'not an array')
        end.to raise_error(ArgumentError, 'handwriting must be an array')
      end
    end
  end

  describe 'Bias' do
    subject(:bias_class) { described_class::Bias }

    context 'with valid attributes' do
      let(:bias) do
        bias_class.new(
          level: 'high',
          type: 'gender',
          explanation: 'Contains gender stereotypes'
        )
      end

      it 'creates instance with valid attributes' do
        expect(bias.level).to eq('high')
        expect(bias.type).to eq('gender')
        expect(bias.explanation).to eq('Contains gender stereotypes')
      end

      it 'converts to hash' do
        expect(bias.to_h).to eq({
          level: 'high',
          type: 'gender',
          explanation: 'Contains gender stereotypes'
        })
      end
    end

    context 'with invalid attributes' do
      it 'raises error for invalid bias level' do
        expect do
          bias_class.new(level: 'invalid', type: 'gender', explanation: 'test')
        end.to raise_error(ArgumentError, 'Invalid bias level')
      end

      it 'raises error for invalid bias type' do
        expect do
          bias_class.new(level: 'high', type: 'invalid', explanation: 'test')
        end.to raise_error(ArgumentError, 'Invalid bias type')
      end

      it 'raises error for nil explanation' do
        expect do
          bias_class.new(level: 'high', type: 'gender', explanation: nil)
        end.to raise_error(ArgumentError, 'Explanation is required')
      end

      it 'raises error for empty explanation' do
        expect do
          bias_class.new(level: 'high', type: 'gender', explanation: '')
        end.to raise_error(ArgumentError, 'Explanation is required')
      end
    end
  end

  describe 'Biases' do
    subject(:biases_class) { described_class::Biases }

    let(:bias_class) { described_class::Bias }

    context 'with valid attributes' do
      let(:bias1) { bias_class.new(level: 'low', type: 'age', explanation: 'Minor age bias') }
      let(:bias2) { bias_class.new(level: 'high', type: 'racial', explanation: 'Racial stereotypes') }

      it 'creates instance with array of Bias objects' do
        biases = biases_class.new(biases: [bias1, bias2])
        expect(biases.biases).to contain_exactly(bias1, bias2)
      end

      it 'creates instance with array of hashes' do
        biases = biases_class.new(biases: [
          { 'level' => 'low', 'type' => 'age', 'explanation' => 'Minor age bias' },
          { 'level' => 'high', 'type' => 'racial', 'explanation' => 'Racial stereotypes' }
        ])
        expect(biases.biases.size).to eq(2)
        expect(biases.biases.first).to be_a(bias_class)
      end

      it 'creates instance with empty array' do
        biases = biases_class.new
        expect(biases.biases).to eq([])
      end

      it 'converts to hash' do
        biases = biases_class.new(biases: [bias1])
        expect(biases.to_h).to eq({
          biases: [
            { level: 'low', type: 'age', explanation: 'Minor age bias' }
          ]
        })
      end
    end

    context 'with invalid attributes' do
      it 'raises error for non-array biases' do
        expect do
          biases_class.new(biases: 'not an array')
        end.to raise_error(ArgumentError, 'biases must be an array')
      end

      it 'validates each bias in the array' do
        expect do
          biases_class.new(biases: [
            { 'level' => 'invalid', 'type' => 'gender', 'explanation' => 'test' }
          ])
        end.to raise_error(ArgumentError, 'Invalid bias level')
      end
    end
  end

  describe 'WorkBiasAnalysis' do
    subject(:work_bias_analysis_class) { described_class::WorkBiasAnalysis }

    let(:biases_class) { described_class::Biases }

    context 'with valid attributes' do
      let(:metadata_biases) { biases_class.new(biases: []) }
      let(:page_biases) { [biases_class.new(biases: [])] }

      it 'creates instance with Biases objects' do
        analysis = work_bias_analysis_class.new(
          metadata_biases: metadata_biases,
          page_biases: page_biases
        )
        expect(analysis.metadata_biases).to eq(metadata_biases)
        expect(analysis.page_biases).to eq(page_biases)
      end

      it 'creates instance with hash for metadata_biases' do
        analysis = work_bias_analysis_class.new(
          metadata_biases: { 'biases' => [] },
          page_biases: []
        )
        expect(analysis.metadata_biases).to be_a(biases_class)
      end

      it 'creates instance with array of hashes for page_biases' do
        analysis = work_bias_analysis_class.new(
          metadata_biases: metadata_biases,
          page_biases: [{ 'biases' => [] }]
        )
        expect(analysis.page_biases.first).to be_a(biases_class)
      end

      it 'converts to hash' do
        analysis = work_bias_analysis_class.new(
          metadata_biases: metadata_biases,
          page_biases: page_biases
        )
        expect(analysis.to_h).to eq({
          metadata_biases: { biases: [] },
          page_biases: [{ biases: [] }]
        })
      end
    end

    context 'with invalid attributes' do
      it 'raises error for invalid metadata_biases type' do
        expect do
          work_bias_analysis_class.new(
            metadata_biases: 'invalid',
            page_biases: []
          )
        end.to raise_error(ArgumentError, 'metadata_biases must be a Biases object')
      end

      it 'raises error for non-array page_biases' do
        expect do
          work_bias_analysis_class.new(
            metadata_biases: biases_class.new,
            page_biases: 'not an array'
          )
        end.to raise_error(ArgumentError)
      end
    end
  end

  describe 'DocumentLengthError' do
    subject(:error_class) { described_class::DocumentLengthError }

    it 'creates error with message' do
      error = error_class.new('Document too long')
      expect(error.message).to eq('Document too long')
      expect(error.error_code).to be_nil
    end

    it 'creates error with message and code' do
      error = error_class.new('Document too long', 'DOC_001')
      expect(error.message).to eq('Document too long')
      expect(error.error_code).to eq('DOC_001')
    end
  end
end
