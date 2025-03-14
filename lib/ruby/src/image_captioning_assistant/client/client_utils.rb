# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'json'
require 'logger'
require 'net/http'
require 'uri'

# Client utils for the api_gateway_demo notebook.
class ApiClient
  def initialize
    @logger = Logger.new(STDOUT)
  end

  def submit_job(api_url, job_name, job_type, works, api_key)
    # Construct the full URL
    api_url = api_url.sub(%r{/+$}, '')
    endpoint = "#{api_url}/create_job"
    uri = URI(endpoint)

    # Headers and body
    headers = {
      'Content-Type' => 'application/json',
      'x-api-key' => api_key
    }
    request_body = {
      job_name: job_name,
      job_type: job_type,
      works: works
    }.to_json

    # Make the POST request
    response = make_request(Net::HTTP::Post, uri, headers, request_body)
    JSON.parse(response.body)
  end

  def get_job_progress(api_url, job_name, api_key)
    # Construct the full URL
    api_url = api_url.sub(%r{/+$}, '')
    endpoint = "#{api_url}/job_progress"
    uri = URI(endpoint)
    uri.query = URI.encode_www_form(job_name: job_name)

    # Headers
    headers = { 'x-api-key' => api_key }

    # Make the GET request
    response = make_request(Net::HTTP::Get, uri, headers)

    if response.code == '404'
      @logger.error("Error: API request failed with status code #{response.code}")
      return JSON.parse(response.body)
    end

    JSON.parse(response.body)
  end

  def get_overall_progress(api_url, api_key)
    # Construct the full URL
    api_url = api_url.sub(%r{/+$}, '')
    endpoint = "#{api_url}/overall_progress"
    uri = URI(endpoint)

    # Headers
    headers = { 'x-api-key' => api_key }

    # Make the GET request
    response = make_request(Net::HTTP::Get, uri, headers)
    JSON.parse(response.body)
  end

  def get_job_results(api_url, job_name, work_id, api_key)
    # Construct the full URL
    api_url = api_url.sub(%r{/+$}, '')
    endpoint = "#{api_url}/results"
    uri = URI(endpoint)
    uri.query = URI.encode_www_form(job_name: job_name, work_id: work_id)

    # Headers
    headers = { 'x-api-key' => api_key }

    # Make the GET request
    response = make_request(Net::HTTP::Get, uri, headers)
    JSON.parse(response.body)
  end

  def update_job_results(api_url, job_name, work_id, api_key, updated_fields)
    # Construct the full URL
    api_url = api_url.sub(%r{/+$}, '')
    endpoint = "#{api_url}/results"
    uri = URI(endpoint)

    # Headers and body
    headers = {
      'Content-Type' => 'application/json',
      'x-api-key' => api_key
    }
    request_body = {
      job_name: job_name,
      work_id: work_id,
      updated_fields: updated_fields
    }.to_json

    # Make the PUT request
    response = make_request(Net::HTTP::Put, uri, headers, request_body)
    JSON.parse(response.body)
  end

  private

  def make_request(request_class, uri, headers, body = nil)
    http = Net::HTTP.new(uri.host, uri.port)
    http.use_ssl = (uri.scheme == 'https')

    request = request_class.new(uri)
    headers.each { |key, value| request[key] = value }
    request.body = body if body

    response = http.request(request)

    return response if response.is_a?(Net::HTTPSuccess)

    @logger.error("Error: API request failed with status code #{response.code}")
    @logger.error("Response: #{response.body}")

    return response if response.code == '404' && request_class == Net::HTTP::Get

    raise "API request failed: #{response.code} #{response.message}"
  end
end
