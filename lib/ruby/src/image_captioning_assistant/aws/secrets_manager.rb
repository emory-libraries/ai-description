# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

begin
  require 'aws-sdk-secretsmanager'
  SECRETS_MANAGER_AVAILABLE = true
rescue LoadError
  SECRETS_MANAGER_AVAILABLE = false
end

require 'json'

module ImageCaptioningAssistant
  module AWS
    # Secrets Manager utility functions
    module SecretsManager
      # Get secret from AWS Secrets Manager
      # @param secret_name [String] Name of the secret
      # @param region_name [String] AWS region name
      # @return [Hash] Secret value as a hash
      def self.get_secret(secret_name, region_name)
        unless SECRETS_MANAGER_AVAILABLE
          raise "aws-sdk-secretsmanager gem is not available. This functionality requires the gem to be installed."
        end
        
        # Create a Secrets Manager client
        client = Aws::SecretsManager::Client.new(region: region_name)

        begin
          get_secret_value_response = client.get_secret_value(secret_id: secret_name)
        rescue Aws::SecretsManager::Errors::ServiceError => e
          raise e
        else
          # Decrypts secret using the associated KMS key
          if get_secret_value_response.secret_string
            secret = get_secret_value_response.secret_string
            return JSON.parse(secret)
          else
            raise ValueError, "Unexpected secret format"
          end
        end
      end
    end
  end
end