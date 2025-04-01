#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'aws_ai_post_processor'

if ARGV.empty?
  puts "Exiting -- This script must be in the following format:"
  puts "./convert_ai_csv_to_ingest.rb <full path to the CSV file>"
  exit 1
end

csv_path = ARGV[0]

AwsAiPostProcessor.new(csv_path).process
