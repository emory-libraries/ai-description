# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

require 'logger'

module ImageCaptioningAssistant
  # Shared logger for the entire module
  module Logging
    def self.logger
      @logger ||= Logger.new($stdout).tap do |log|
        log.level = Logger::INFO
      end
    end
  end
end
