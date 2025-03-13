# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

module ImageCaptioningAssistant
  require_relative 'image_captioning_assistant/data/data_classes'
  require_relative 'image_captioning_assistant/aws/s3'
  
  def self.load_module(module_path)
    require_relative module_path
  rescue LoadError => e
    puts "Warning: Could not load module #{module_path}: #{e.message}"
  end
  
  load_module 'image_captioning_assistant/aws/secrets_manager'
  
  Dir[File.join(File.dirname(__FILE__), 'image_captioning_assistant', 'generate', '**', '*.rb')].sort.each do |file|
    require file
  end
end