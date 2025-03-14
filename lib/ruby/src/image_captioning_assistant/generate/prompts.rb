# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

module ImageCaptioningAssistant
  module Generate
    module Prompts
      COT_TAG_NAME = 'object_detail_and_bias_analysis'
      COT_TAG = "<#{COT_TAG_NAME}>"
      COT_TAG_END = "</#{COT_TAG_NAME}>"

      ASSISTANT_START = COT_TAG
      ASSISTANT_START_COURT_ORDER = COT_TAG

      SYSTEM_PROMPT = File.read(File.join(File.dirname(__FILE__), 'prompt_templates/system_prompt.txt'))
      SYSTEM_PROMPT_COURT_ORDER = File.read(File.join(File.dirname(__FILE__), 'prompt_templates/system_prompt_court_order.txt'))

      USER_PROMPT_METADATA = File.read(File.join(File.dirname(__FILE__), 'prompt_templates/user_prompt_metadata.txt'))
      USER_PROMPT_BIAS = File.read(File.join(File.dirname(__FILE__), 'prompt_templates/user_prompt_bias.erb'))
    end
  end
end
