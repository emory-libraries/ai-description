#!/usr/bin/env ruby
# frozen_string_literal: true

require_relative 'aws_ai_csv_processor'

if ARGV.empty?
  puts "Exiting -- This script must be in the following format:"
  puts "./extract_aws_files_to_csv.rb <full path to the CSV file>"
  exit 1
end

csv_path = ARGV[0]

AwsAiCsvProcessor.new(csv_path).process_all_pages_in_works
