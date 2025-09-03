# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

FactoryBot.define do
  factory :explained_value, class: 'ImageCaptioningAssistant::Data::ExplainedValue' do
    value { Faker::Lorem.word }
    explanation { Faker::Lorem.sentence }

    initialize_with { new(value: value, explanation: explanation) }
  end

  factory :page_transcription, class: 'ImageCaptioningAssistant::Data::PageTranscription' do
    printed_text { [Faker::Lorem.paragraph, Faker::Lorem.paragraph] }
    handwriting { [Faker::Lorem.sentence] }

    initialize_with { new(printed_text: printed_text, handwriting: handwriting) }
  end

  factory :transcription, class: 'ImageCaptioningAssistant::Data::Transcription' do
    transcriptions { build_list(:page_transcription, 2) }
    model_notes { Faker::Lorem.sentence }

    initialize_with { new(transcriptions: transcriptions, model_notes: model_notes) }
  end

  factory :metadata, class: 'ImageCaptioningAssistant::Data::Metadata' do
    description { build(:explained_value) }
    transcription { build(:transcription) }
    date { build(:explained_value, value: '1920s') }
    location { build(:explained_value, value: 'New York') }
    publication_info { build(:explained_value, value: 'Publisher Inc.') }
    contextual_info { build(:explained_value) }
    format { build(:explained_value, value: 'Still Image') }
    genre { build(:explained_value, value: 'Photography') }
    objects { build(:explained_value, value: 'Building, Car') }
    actions { build(:explained_value, value: 'Standing, Walking') }
    people { build(:explained_value, value: 'Group of people') }
    topics { build(:explained_value, value: 'Urban life') }

    initialize_with do
      new(
        description: description,
        transcription: transcription,
        date: date,
        location: location,
        publication_info: publication_info,
        contextual_info: contextual_info,
        format: format,
        genre: genre,
        objects: objects,
        actions: actions,
        people: people,
        topics: topics
      )
    end
  end

  factory :bias, class: 'ImageCaptioningAssistant::Data::Bias' do
    level { %w[low medium high].sample }
    type { %w[gender racial cultural age].sample }
    explanation { Faker::Lorem.sentence }

    initialize_with { new(level: level, type: type, explanation: explanation) }

    trait :low do
      level { 'low' }
    end

    trait :medium do
      level { 'medium' }
    end

    trait :high do
      level { 'high' }
    end

    trait :gender do
      type { 'gender' }
    end

    trait :racial do
      type { 'racial' }
    end
  end

  factory :biases, class: 'ImageCaptioningAssistant::Data::Biases' do
    biases { build_list(:bias, 2) }

    initialize_with { new(biases: biases) }

    trait :empty do
      biases { [] }
    end

    trait :with_high_biases do
      biases { build_list(:bias, 3, :high) }
    end
  end

  factory :work_bias_analysis, class: 'ImageCaptioningAssistant::Data::WorkBiasAnalysis' do
    metadata_biases { build(:biases) }
    page_biases { build_list(:biases, 2) }

    initialize_with { new(metadata_biases: metadata_biases, page_biases: page_biases) }

    trait :no_biases do
      metadata_biases { build(:biases, :empty) }
      page_biases { [build(:biases, :empty)] }
    end

    trait :high_biases do
      metadata_biases { build(:biases, :with_high_biases) }
      page_biases { build_list(:biases, 2, :with_high_biases) }
    end
  end
end
