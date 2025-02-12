# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data classes used throughout the metadata generation process."""

from typing import List

from image_captioning_assistant.data.constants import BiasLevel, BiasType
from pydantic import BaseModel, Field


class PotentialBias(BaseModel):
    """A potential bias present in an image."""

    bias_type: BiasType = Field(..., description="The type of bias exibited by the image")
    bias_level: BiasLevel = Field(..., description="The level of bias exibited by the image")
    explanation: str = Field(..., description="Freeform commentary on the bias recognized in the image")


BiasAnalysis = List[PotentialBias]


class StructuredMetadata(BaseModel):
    """Metadata fields for an image.

    This is the metadata requested for items in the Langmuir collection.
    """

    description: str = Field(..., description="A description of the contents of an image")
    transcription: str = Field(..., description="A transcription of any text in the image")
    people_and_groups: list[str] = Field(..., description="The names of any people or groups recognized in the image")
    date: str = Field(..., description="The approximate date the image may have been taken")
    location: str = Field(..., description="The approximate location where the image may have been taken")
    publication_info: str = Field(..., description="Any known publication information")
    contextual_info: str = Field(..., description="Any known contextual information around the image")
    potential_biases: BiasAnalysis = Field(..., description="A list of any potential biases present in the image")
