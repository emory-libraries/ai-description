# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'

RSpec.describe ImageCaptioningAssistant::Data::Constants do
  describe 'BiasLevel' do
    subject(:bias_level) { described_class::BiasLevel }

    it 'defines LOW level' do
      expect(bias_level::LOW).to eq('low')
    end

    it 'defines MEDIUM level' do
      expect(bias_level::MEDIUM).to eq('medium')
    end

    it 'defines HIGH level' do
      expect(bias_level::HIGH).to eq('high')
    end

    describe '.all' do
      it 'returns all bias levels' do
        expect(bias_level.all).to contain_exactly('low', 'medium', 'high')
      end
    end
  end

  describe 'BiasType' do
    subject(:bias_type) { described_class::BiasType }

    it 'defines all expected bias types' do
      expect(bias_type::GENDER).to eq('gender')
      expect(bias_type::RACIAL).to eq('racial')
      expect(bias_type::SEXUAL).to eq('sexual')
      expect(bias_type::CULTURAL).to eq('cultural')
      expect(bias_type::ABILITY).to eq('ability')
      expect(bias_type::SEXUAL_ORIENTATION).to eq('sexual orientation')
      expect(bias_type::BODY_SHAPE).to eq('body shape')
      expect(bias_type::AGE).to eq('age')
      expect(bias_type::VIOLENCE).to eq('violence')
      expect(bias_type::POLITICAL).to eq('political')
      expect(bias_type::NUDITY).to eq('nudity')
      expect(bias_type::OTHER).to eq('other')
    end

    describe '.all' do
      it 'returns all bias types' do
        all_types = bias_type.all
        expect(all_types).to include('gender', 'racial', 'sexual', 'cultural')
        expect(all_types.size).to eq(12)
      end
    end
  end

  describe 'LibraryFormat' do
    subject(:library_format) { described_class::LibraryFormat }

    it 'defines all expected formats' do
      expect(library_format::ARTIFACT).to eq('Artifact')
      expect(library_format::AUDIO).to eq('Audio')
      expect(library_format::CARTOGRAPHIC).to eq('Cartographic')
      expect(library_format::COLLECTION).to eq('Collection')
      expect(library_format::DATASET).to eq('Dataset')
      expect(library_format::DIGITAL).to eq('Digital')
      expect(library_format::MANUSCRIPT).to eq('Manuscript')
      expect(library_format::MIXED_MATERIAL).to eq('Mixed Material')
      expect(library_format::MOVING_IMAGE).to eq('Moving Image')
      expect(library_format::MULTIMEDIA).to eq('Multimedia')
      expect(library_format::NOTATED_MUSIC).to eq('Notated Music')
      expect(library_format::STILL_IMAGE).to eq('Still Image')
      expect(library_format::TACTILE).to eq('Tactile')
      expect(library_format::TEXT).to eq('Text')
      expect(library_format::UNSPECIFIED).to eq('Unspecified')
    end

    describe '.all' do
      it 'returns all library formats' do
        all_formats = library_format.all
        expect(all_formats).to include('Artifact', 'Audio', 'Still Image', 'Text')
        expect(all_formats.size).to eq(15)
      end
    end
  end
end
