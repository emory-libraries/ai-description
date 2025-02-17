# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

import os

from jinja2 import Template

COT_TAG_NAME = "object_detail_and_bias_analysis"
COT_TAG = f"<{COT_TAG_NAME}>"
COT_TAG_END = f"</{COT_TAG_NAME}>"

current_dir = os.path.dirname(__file__)

with open(os.path.join(current_dir, "system_prompt.txt"), "r") as file:
    system_prompt = file.read()

with open(os.path.join(current_dir, "user_prompt.txt"), "r") as file:
    user_prompt = Template(file.read()).render(COT_TAG=COT_TAG, COT_TAG_END=COT_TAG_END, COT_TAG_NAME=COT_TAG_NAME)

with open(os.path.join(current_dir, "user_prompt_bias_only.txt"), "r") as file:
    user_prompt_bias_only = Template(file.read()).render(
        COT_TAG=COT_TAG, COT_TAG_END=COT_TAG_END, COT_TAG_NAME=COT_TAG_NAME
    )

assistant_start = COT_TAG
