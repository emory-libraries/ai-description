# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.
import json
import os

from jinja2 import Template

import image_captioning_assistant.data.data_classes as dc

COT_TAG_NAME = "object_detail_and_bias_analysis"
COT_TAG = f"<{COT_TAG_NAME}>"
COT_TAG_END = f"</{COT_TAG_NAME}>"

current_dir = os.path.dirname(__file__)

# dump metadata definition for prompt
METADATA_MODEL_DUMP = json.dumps(dc.Metadata.model_json_schema(), indent=4, ensure_ascii=False)

with open(os.path.join(current_dir, "system_prompt.txt"), "r") as file:
    system_prompt = file.read()


with open(os.path.join(current_dir, "system_prompt_court_order.txt"), "r") as file:
    system_prompt_court_order = file.read()

with open(os.path.join(current_dir, "user_prompt_metadata.txt"), "r") as file:
    user_prompt_metadata = Template(file.read(), autoescape=True).render(
        COT_TAG=COT_TAG, COT_TAG_END=COT_TAG_END, COT_TAG_NAME=COT_TAG_NAME, PYDANTIC_MODEL_DUMP=METADATA_MODEL_DUMP
    )


with open(os.path.join(current_dir, "user_prompt_bias_only.jinja"), "r") as file:
    user_prompt_bias_only = Template(file.read(), autoescape=True).render(
        COT_TAG=COT_TAG, COT_TAG_END=COT_TAG_END, COT_TAG_NAME=COT_TAG_NAME
    )

assistant_start = COT_TAG

assistant_start_court_order = COT_TAG
