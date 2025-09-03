# frozen_string_literal: true

# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'simplecov'
SimpleCov.start do
  add_filter '/spec/'
  add_filter '/vendor/'
  add_group 'AWS', 'src/image_captioning_assistant/aws'
  add_group 'Client', 'src/image_captioning_assistant/client'
  add_group 'Data', 'src/image_captioning_assistant/data'
  add_group 'Generate', 'src/image_captioning_assistant/generate'
end

require 'webmock/rspec'
require 'factory_bot'
require 'faker'
require 'pry'

# Load the main library
$LOAD_PATH.unshift File.expand_path('../src', __dir__)
require 'image_captioning_assistant'

# Load additional client files that aren't auto-loaded
require 'image_captioning_assistant/client/client_utils'
require 'image_captioning_assistant/client/data_prep'

# Configure RSpec
RSpec.configure do |config|
  config.expect_with :rspec do |expectations|
    expectations.include_chain_clauses_in_custom_matcher_descriptions = true
  end

  config.mock_with :rspec do |mocks|
    mocks.verify_partial_doubles = true
  end

  config.shared_context_metadata_behavior = :apply_to_host_groups
  config.filter_run_when_matching :focus
  config.example_status_persistence_file_path = 'spec/examples.txt'
  config.disable_monkey_patching!
  config.warnings = true

  config.default_formatter = 'doc' if config.files_to_run.one?

  config.profile_examples = 10
  config.order = :random
  Kernel.srand config.seed

  # Include FactoryBot methods
  config.include FactoryBot::Syntax::Methods

  config.before(:suite) do
    FactoryBot.find_definitions
  end

  # WebMock configuration
  config.before do
    WebMock.disable_net_connect!(allow_localhost: true)
  end

  config.after do
    WebMock.reset!
  end
end

# Helper methods available to all specs
module SpecHelpers
  def fixture_path(filename)
    File.join(File.dirname(__FILE__), 'fixtures', filename)
  end

  def load_fixture(filename)
    File.read(fixture_path(filename))
  end

  def load_binary_fixture(filename)
    File.binread(fixture_path(filename))
  end

  def stub_aws_credentials
    allow(ENV).to receive(:[]).and_call_original
    allow(ENV).to receive(:[]).with('AWS_ACCESS_KEY_ID').and_return('test-access-key')
    allow(ENV).to receive(:[]).with('AWS_SECRET_ACCESS_KEY').and_return('test-secret-key')
    allow(ENV).to receive(:[]).with('AWS_REGION').and_return('us-east-1')
  end

  def create_test_image_bytes
    # Create a simple 1x1 pixel JPEG image
    "\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" \
      "\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t" \
      "\x08\n\x0C\x14\r\x0C\x0B\x0B\x0C\x19\x12\x13\x0F\x14\x1D\x1A" \
      "\x1F\x1E\x1D\x1A\x1C\x1C $.' \",#\x1C\x1C(7),01444\x1F'9=82<.342" \
      "\xFF\xC0\x00\x0B\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00" \
      "\x1F\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00" \
      "\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0B\xFF\xC4\x00" \
      "\xB5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00" \
      "\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81" \
      "\x91\xA1\x08#B\xB1\xC1\x15R\xD1\xF0$3br\x82\t\n\x16\x17\x18\x19" \
      "\x1A%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86" \
      "\x87\x88\x89\x8A\x92\x93\x94\x95\x96\x97\x98\x99\x9A\xA2\xA3\xA4" \
      "\xA5\xA6\xA7\xA8\xA9\xAA\xB2\xB3\xB4\xB5\xB6\xB7\xB8\xB9\xBA\xC2" \
      "\xC3\xC4\xC5\xC6\xC7\xC8\xC9\xCA\xD2\xD3\xD4\xD5\xD6\xD7\xD8\xD9" \
      "\xDA\xE1\xE2\xE3\xE4\xE5\xE6\xE7\xE8\xE9\xEA\xF1\xF2\xF3\xF4\xF5" \
      "\xF6\xF7\xF8\xF9\xFA\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\xFB\xD0" \
      "\xFF\xD9"
  end
end

RSpec.configure do |config|
  config.include SpecHelpers
end
