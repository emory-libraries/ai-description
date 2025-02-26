# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Pydantic models for metadata generation and bias analysis.

This module contains structured data definitions for:
- Image/artifact transcriptions
- Cultural heritage metadata
- Bias analysis framework
- Composite structured metadata format
"""

from typing import Annotated, Generic, List, TypeVar

from pydantic import BaseModel, BeforeValidator, Field
from pydantic.functional_validators import AfterValidator

from image_captioning_assistant.data.constants import BiasLevel, BiasType, LibraryFormat

ValueType = TypeVar("ValueType")


class ExplainedValue(BaseModel, Generic[ValueType]):
    """Generic container for typed values with LLM explanations"""

    value: ValueType
    explanation: str = Field(..., description="LLM's reasoning for providing this specific value")

    @classmethod
    def with_type(cls, value_type: type[ValueType]) -> type["ExplainedValue"]:
        """Type helper for creating field-specific variants"""

        class ConcreteExplainedValue(ExplainedValue[ValueType]):
            value: value_type  # type: ignore

        return ConcreteExplainedValue


class PageTranscription(BaseModel):
    """Container for transcribed text elements in a page with preservation of original layout."""

    printed_text: List[str] = Field(..., description="Printed text elements in their original layout/sequence")
    handwriting: List[str] = Field(..., description="Handwritten elements with original spelling/punctuation")


class Transcription(BaseModel):
    """Container for transcribed text elements in multiple pages with notes from the model."""

    transcriptions: List[PageTranscription] = Field(..., description="PageTranscription per page")
    model_notes: str = Field(..., description="Notes to be called out or reviewed per the LLM")


class Metadata(BaseModel):
    """Primary metadata container for cultural heritage materials."""

    description: ExplainedValue[str] = Field(
        ..., description="Detailed accessibility-focused description of visual content"
    )
    transcription: Transcription = Field(..., description="Complete transcription of all legible text elements")
    date: ExplainedValue[str] = Field(..., description="Date of creation (circa dates or ranges acceptable)")
    location: ExplainedValue[List[str]] = Field(..., description="List of locations depicted in content")
    publication_info: ExplainedValue[str] = Field(..., description="Production/publishing context if documented")
    contextual_info: ExplainedValue[str] = Field(..., description="Cultural/historical context of creation or subject")
    format: ExplainedValue[LibraryFormat] = Field(..., description="Physical/digital format category")
    genre: ExplainedValue[List[str]] = Field(..., description="Formal/genre classifications")
    objects: ExplainedValue[List[str]] = Field(
        ..., description="Foreground objects critical to understanding the content"
    )
    actions: ExplainedValue[List[str]] = Field(..., description="Primary actions depicted in the content")
    people: ExplainedValue[List[str]] = Field(..., description="Visible human subjects using specific descriptors")
    topics: ExplainedValue[List[str]] = Field(..., description="Clear high level topics")


class MetadataCOT(Metadata):
    """Composite metadata structure combining Chain of Thought and Metadata."""

    cot: str = Field(..., description="Chain of thought of model")


class Bias(BaseModel):
    """Individual bias assessment with classification and contextual explanation."""

    level: BiasLevel = Field(..., description="Potential harm classification")
    type: BiasType = Field(..., description="Category of bias identified")
    explanation: str = Field(..., description="Contextual analysis of bias manifestation")


class Biases(BaseModel):
    """All biases detected."""

    biases: list[Bias] = Field(default_factory=list, description="All biases detected")


class WorkBiasAnalysis(BaseModel):
    """Bias analysis for an entire work."""

    metadata_biases: Biases = Field(..., description="Biases in the metadata itself")
    page_biases: list[Biases] = Field(..., description="Biases found in each page of a work")


class BiasAnalysisCOT(Biases):
    """Composite metadata structure combining Chain of Thought and Bias Analysis."""

    cot: str = Field(..., description="Chain of thought of model")


class WorkBiasAnalysisCOT(WorkBiasAnalysis):
    """Composite metadata structure combining Chain of Thought and WorkBiasAnalysis"""

    cot: str = Field(..., description="Chain of thought of model")


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
