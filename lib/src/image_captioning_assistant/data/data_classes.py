# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data classes used throughout the metadata generation process."""

from typing import List, Literal

from image_captioning_assistant.data.constants import BiasLevel, BiasType
from pydantic import BaseModel, Field


# class PotentialBias(BaseModel):
#     """A potential bias present in an image."""

#     bias_type: BiasType = Field(..., description="The type of bias exibited by the image")
#     bias_level: BiasLevel = Field(..., description="The level of bias exibited by the image")
#     explanation: str = Field(..., description="Freeform commentary on the bias recognized in the image")


# BiasAnalysis = List[PotentialBias]


# class StructuredMetadata(BaseModel):
#     """Metadata fields for an image.

#     This is the metadata requested for items in the Langmuir collection.
#     """

#     description: str = Field(..., description="A description of the contents of an image")
#     transcription: str = Field(..., description="A transcription of any text in the image")
#     people_and_groups: list[str] = Field(..., description="The names of any people or groups recognized in the image")
#     date: str = Field(..., description="The approximate date the image may have been taken")
#     location: str = Field(..., description="The approximate location where the image may have been taken")
#     publication_info: str = Field(..., description="Any known publication information")
#     contextual_info: str = Field(..., description="Any known contextual information around the image")
#     potential_biases: BiasAnalysis = Field(..., description="A list of any potential biases present in the image")

class Transcription(BaseModel):
    print: List[str] = Field(
        ...,
        description="Printed text elements in their original layout/sequence"
    )
    handwriting: List[str] = Field(
        ...,
        description="Handwritten elements with original spelling/punctuation"
    )

class Metadata(BaseModel):
    description: str = Field(
        ...,
        description="Detailed accessibility-focused description of visual content",
    )
    transcription: Transcription = Field(
        ...,
        description="Complete transcription of all legible text elements"
    )
    date: str = Field(
        ...,
        description="Date of creation (circa dates or ranges acceptable)"
    )
    location_information: str = Field(
        ...,
        description="Geographic context of depicted content"
    )
    publication_info: List[str] = Field(
        ...,
        description="Production/publishing context if documented"
    )
    contextual_info: List[str] = Field(
        ...,
        description="Cultural/historical context of creation or subject"
    )
    format: Literal[
        "Still Image", 
        "Text", 
        "Artifact", 
        "Cartographic", 
        "Notated Music", 
        "Mixed Material"
    ] = Field(..., description="Physical/digital format category")
    genre: List[str] = Field(
        ...,
        description="Formal/genre classifications",
    )
    objects: List[str] = Field(
        ...,
        description="Foreground objects critical to understanding the content",
    )
    actions: List[str] = Field(
        ...,
        description="Primary actions depicted in the content",
    )
    people: List[str] = Field(
        ...,
        description="Visible human subjects using specific descriptors",
        examples=["Black woman", "White male child"]
    )

class BiasAnalysisEntry(BaseModel):
    bias_level: Literal["Low", "Medium", "High"] = Field(
        ...,
        description="Potential harm classification"
    )
    bias_type: Literal[
        "gender", 
        "racial", 
        "sexual", 
        "cultural", 
        "ableist",
        "sexual_orientation", 
        "ageism", 
        "violence", 
        "political", 
        "other"
    ] = Field(..., description="Category of bias identified")
    explanation: str = Field(
        ...,
        description="Contextual analysis of bias manifestation",
    )

BiasAnalysis = List[BiasAnalysisEntry]

class StructuredMetadata(BaseModel):
    object_detail_and_bias_analysis: str = Field(..., description="Step by step reasoning process")
    metadata: Metadata = Field(..., description="Metadata")
    bias_analysis: BiasAnalysis = Field(
        ...,
        description="Multiple bias evaluations allowed",
    )
