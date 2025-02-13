# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Data classes used throughout the metadata generation process."""

from typing import List, Literal

from image_captioning_assistant.data.constants import BiasLevel, BiasType
from pydantic import BaseModel, Field


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
    location: str = Field(
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
    # object_detail_and_bias_analysis: str = Field(..., description="Step by step reasoning process")
    metadata: Metadata = Field(..., description="Metadata")
    bias_analysis: BiasAnalysis = Field(
        ...,
        description="Multiple bias evaluations allowed",
    )
