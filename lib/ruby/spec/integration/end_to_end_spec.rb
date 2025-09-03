# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'

RSpec.describe 'End-to-end workflow', :integration do
  before do
    stub_aws_credentials
  end

  describe 'S3 integration' do
    let(:s3_client) { instance_double(Aws::S3::Client) }
    let(:bucket) { 'test-bucket' }
    let(:key) { 'test-image.jpg' }

    before do
      allow(Aws::S3::Client).to receive(:new).and_return(s3_client)
    end

    it 'loads and processes an image from S3' do
      # Stub S3 response
      response = instance_double(Aws::S3::Types::GetObjectOutput)
      allow(response).to receive(:body).and_return(StringIO.new(create_test_image_bytes))
      allow(s3_client).to receive(:get_object).and_return(response)

      # Load image
      image_bytes = ImageCaptioningAssistant::AWS::S3.load_to_bytes(
        s3_bucket: bucket,
        s3_key: key
      )

      expect(image_bytes).not_to be_empty
      # The S3 module returns UTF-8 encoded strings
      expect(image_bytes).to be_a(String)
    end
  end

  describe 'Data structure creation' do
    it 'creates a complete metadata object' do
      metadata = build(:metadata)

      expect(metadata).to be_a(ImageCaptioningAssistant::Data::Metadata)
      expect(metadata.description).to be_a(ImageCaptioningAssistant::Data::ExplainedValue)
      expect(metadata.transcription).to be_a(ImageCaptioningAssistant::Data::Transcription)

      # Verify it can be converted to hash
      hash = metadata.to_h
      expect(hash).to be_a(Hash)
      expect(hash[:description]).to have_key(:value)
      expect(hash[:description]).to have_key(:explanation)
    end

    it 'creates a work bias analysis' do
      analysis = build(:work_bias_analysis, :high_biases)

      expect(analysis).to be_a(ImageCaptioningAssistant::Data::WorkBiasAnalysis)
      expect(analysis.metadata_biases.biases).not_to be_empty
      expect(analysis.page_biases).not_to be_empty

      # Verify serialization
      hash = analysis.to_h
      expect(hash[:metadata_biases][:biases]).to be_an(Array)
      expect(hash[:page_biases]).to be_an(Array)
    end
  end

  describe 'API client workflow' do
    let(:api_client) { ApiClient.new }
    let(:api_url) { 'https://api.example.com' }
    let(:api_key) { 'test-key' }

    it 'completes a job submission workflow' do
      job_name = 'test-job'
      job_type = 'metadata'
      works = [
        {
          work_id: 'work-001',
          image_s3_uris: ['s3://bucket/image1.jpg'],
          original_metadata_s3_uri: 's3://bucket/metadata.json'
        }
      ]

      # Stub job creation
      stub_request(:post, "#{api_url}/create_job")
        .to_return(
          status: 200,
          body: { job_id: 'job-123', status: 'created' }.to_json
        )

      # Stub progress check
      stub_request(:get, "#{api_url}/job_progress")
        .with(query: { job_name: job_name })
        .to_return(
          status: 200,
          body: {
            job_name: job_name,
            progress: 100,
            status: 'completed',
            completed_works: 1,
            total_works: 1
          }.to_json
        )

      # Stub results retrieval
      stub_request(:get, "#{api_url}/results")
        .with(query: { job_name: job_name, work_id: 'work-001' })
        .to_return(
          status: 200,
          body: {
            work_id: 'work-001',
            metadata: {
              description: { value: 'Test image', explanation: 'Generated description' }
            },
            bias_analysis: {
              metadata_biases: { biases: [] },
              page_biases: [{ biases: [] }]
            }
          }.to_json
        )

      # Execute workflow
      # 1. Submit job
      submission_result = api_client.submit_job(api_url, job_name, job_type, works, api_key)
      expect(submission_result['status']).to eq('created')

      # 2. Check progress
      progress = api_client.get_job_progress(api_url, job_name, api_key)
      expect(progress['status']).to eq('completed')
      expect(progress['progress']).to eq(100)

      # 3. Get results
      results = api_client.get_job_results(api_url, job_name, 'work-001', api_key)
      expect(results['work_id']).to eq('work-001')
      expect(results['metadata']).to be_a(Hash)
      expect(results['bias_analysis']).to be_a(Hash)
    end
  end
end
