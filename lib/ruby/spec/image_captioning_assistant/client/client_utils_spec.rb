# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'spec_helper'
require 'net/http'

RSpec.describe ApiClient do
  let(:api_client) { described_class.new }
  let(:api_url) { 'https://api.example.com' }
  let(:api_key) { 'test-api-key' }

  describe '#submit_job' do
    let(:job_name) { 'test-job' }
    let(:job_type) { 'metadata' }
    let(:works) { [{ work_id: '123', image_s3_uris: ['s3://bucket/image.jpg'] }] }

    before do
      stub_request(:post, "#{api_url}/create_job")
        .with(
          headers: { 'Content-Type' => 'application/json', 'x-api-key' => api_key },
          body: { job_name: job_name, job_type: job_type, works: works }.to_json
        )
        .to_return(
          status: 200,
          body: { job_id: 'job-123', status: 'created' }.to_json
        )
    end

    it 'submits job successfully' do
      result = api_client.submit_job(api_url, job_name, job_type, works, api_key)
      expect(result).to eq({ 'job_id' => 'job-123', 'status' => 'created' })
    end

    it 'strips trailing slashes from URL' do
      stub_request(:post, 'https://api.example.com/create_job')
        .to_return(status: 200, body: {}.to_json)

      api_client.submit_job("#{api_url}/", job_name, job_type, works, api_key)
      expect(WebMock).to have_requested(:post, 'https://api.example.com/create_job')
    end

    context 'when request fails' do
      before do
        stub_request(:post, "#{api_url}/create_job")
          .to_return(status: 500, body: 'Internal Server Error')
      end

      it 'raises an error' do
        expect do
          api_client.submit_job(api_url, job_name, job_type, works, api_key)
        end.to raise_error(/API request failed/)
      end
    end
  end

  describe '#get_job_progress' do
    let(:job_name) { 'test-job' }

    before do
      stub_request(:get, "#{api_url}/job_progress")
        .with(
          query: { job_name: job_name },
          headers: { 'x-api-key' => api_key }
        )
        .to_return(
          status: 200,
          body: { job_name: job_name, progress: 50, status: 'processing' }.to_json
        )
    end

    it 'gets job progress successfully' do
      result = api_client.get_job_progress(api_url, job_name, api_key)
      expect(result).to eq({
        'job_name' => job_name,
        'progress' => 50,
        'status' => 'processing'
      })
    end

    context 'when job not found' do
      before do
        stub_request(:get, "#{api_url}/job_progress")
          .with(query: { job_name: job_name })
          .to_return(
            status: 404,
            body: { error: 'Job not found' }.to_json
          )
      end

      it 'returns error response without raising' do
        result = api_client.get_job_progress(api_url, job_name, api_key)
        expect(result).to eq({ 'error' => 'Job not found' })
      end
    end
  end

  describe '#get_overall_progress' do
    before do
      stub_request(:get, "#{api_url}/overall_progress")
        .with(headers: { 'x-api-key' => api_key })
        .to_return(
          status: 200,
          body: { total_jobs: 10, completed: 5, in_progress: 3 }.to_json
        )
    end

    it 'gets overall progress successfully' do
      result = api_client.get_overall_progress(api_url, api_key)
      expect(result).to eq({
        'total_jobs' => 10,
        'completed' => 5,
        'in_progress' => 3
      })
    end
  end

  describe '#get_job_results' do
    let(:job_name) { 'test-job' }
    let(:work_id) { 'work-123' }

    before do
      stub_request(:get, "#{api_url}/results")
        .with(
          query: { job_name: job_name, work_id: work_id },
          headers: { 'x-api-key' => api_key }
        )
        .to_return(
          status: 200,
          body: {
            job_name: job_name,
            work_id: work_id,
            metadata: { title: 'Test Work' }
          }.to_json
        )
    end

    it 'gets job results successfully' do
      result = api_client.get_job_results(api_url, job_name, work_id, api_key)
      expect(result).to include(
        'job_name' => job_name,
        'work_id' => work_id,
        'metadata' => { 'title' => 'Test Work' }
      )
    end
  end

  describe '#update_job_results' do
    let(:job_name) { 'test-job' }
    let(:work_id) { 'work-123' }
    let(:updated_fields) { { metadata: { title: 'Updated Title' } } }

    before do
      stub_request(:put, "#{api_url}/results")
        .with(
          headers: { 'Content-Type' => 'application/json', 'x-api-key' => api_key },
          body: {
            job_name: job_name,
            work_id: work_id,
            updated_fields: updated_fields
          }.to_json
        )
        .to_return(
          status: 200,
          body: { success: true, message: 'Updated successfully' }.to_json
        )
    end

    it 'updates job results successfully' do
      result = api_client.update_job_results(api_url, job_name, work_id, api_key, updated_fields)
      expect(result).to eq({
        'success' => true,
        'message' => 'Updated successfully'
      })
    end
  end
end
