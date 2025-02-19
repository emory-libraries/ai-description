# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Pydantic models for metadata generation and bias analysis.

This module contains structured data definitions for:
- Image/artifact transcriptions
- Cultural heritage metadata
- Bias analysis framework
- Composite structured metadata format
"""

from typing import List, Optional

from image_captioning_assistant.data.constants import BiasLevel, BiasType, LibraryFormat
from pydantic import BaseModel, Field


class Transcription(BaseModel):
    """Container for transcribed text elements with preservation of original layout."""

    printed_text: List[str] = Field(..., description="Printed text elements in their original layout/sequence")
    handwriting: List[str] = Field(..., description="Handwritten elements with original spelling/punctuation")


class Metadata(BaseModel):
    """Primary metadata container for cultural heritage materials."""

    description: str = Field(..., description="Detailed accessibility-focused description of visual content")
    transcription: Transcription = Field(..., description="Complete transcription of all legible text elements")
    date: str = Field(..., description="Date of creation (circa dates or ranges acceptable)")
    location: str = Field(..., description="Geographic context of depicted content")
    publication_info: List[str] = Field(..., description="Production/publishing context if documented")
    contextual_info: List[str] = Field(..., description="Cultural/historical context of creation or subject")
    format: LibraryFormat = Field(..., description="Physical/digital format category")
    genre: List[str] = Field(..., description="Formal/genre classifications")
    objects: List[str] = Field(..., description="Foreground objects critical to understanding the content")
    actions: List[str] = Field(..., description="Primary actions depicted in the content")
    people: List[str] = Field(..., description="Visible human subjects using specific descriptors")


class MetadataCOT(Metadata):
    """Composite metadata structure combining Chain of Thought and Metadata."""

    cot: str = Field(..., description="Chain of thought of model")


class BiasAnalysisEntry(BaseModel):
    """Individual bias assessment with classification and contextual explanation."""

    bias_level: BiasLevel = Field(..., description="Potential harm classification")
    bias_type: BiasType = Field(..., description="Category of bias identified")
    explanation: str = Field(..., description="Contextual analysis of bias manifestation")


BiasAnalysis = List[BiasAnalysisEntry]


class BiasAnalysisCOT(BaseModel):
    """Composite metadata structure combining Chain of Thought and Bias Analysis."""

    cot: str = Field(..., description="Chain of thought of model")
    bias_analysis: BiasAnalysis = Field(
        ...,
        description="Aggregated bias assessments",
    )


# class StructuredMetadata(BaseModel):
#     """Composite metadata structure combining descriptive and analytical components.
#     Metadata field is optional as generation can happen for only bias analysis.
#     """

#     cot: str = Field(..., description="Chain of thought of model")
#     metadata: Optional[Metadata] = Field(None, description="Core descriptive metadata")
#     bias_analysis: List[BiasAnalysisEntry] = Field(
#         ...,
#         description="Aggregated bias assessments",
#     )
