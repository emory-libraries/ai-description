"""Data classes used throughout the metadata generation process."""

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class BiasLevel(str, Enum):
    """Different levels of bias."""

    none: str = "none"
    # Low potential for harm: unintentional exclusion; gaps or imbalances in the
    # representation of individuals and communities
    low: str = "low"
    # Medium potential for harm: use of obsolete language terms; potential stereotyping that is a
    # result of the historical time period
    medium: str = "medium"
    # High potential for harm: use of offensive terminology, clearly identified
    # racist/sexist/etc. stereotypes and tropes; images of violence or abuse
    high: str = "high"


class BiasType(str, Enum):
    """Different types of bias."""

    gender: str = "gender"
    race: str = "race"
    culture: str = "culture"
    ability: str = "ability"
    sexual_orientation: str = "sexual orientation"
    body_shape: str = "body_shape"
    age: str = "age"
    violence: str = "violence"
    other: str = "other"


class PotentialBias(BaseModel):
    """A potential bias present in an image."""

    bias_type: BiasType = Field(
        ..., description="The type of bias exibited by the image"
    )
    bias_level: BiasLevel = Field(
        ..., description="The level of bias exibited by the image"
    )
    explanation: str = Field(
        ..., description="Freeform commentary on the bias recognized in the image"
    )


BiasAnalysis = List[PotentialBias]


class StructuredMetadata(BaseModel):
    """Metadata fields for an image.

    This is the metadata requested for items in the Langmuir collection.
    """

    description: str = Field(
        ..., description="A description of the contents of an image"
    )
    transcription: str = Field(
        ..., description="A transcription of any text in the image"
    )
    people_and_groups: list[str] = Field(
        ..., description="The names of any people or groups recognized in the image"
    )
    date: str = Field(
        ..., description="The approximate date the image may have been taken"
    )
    location: str = Field(
        ..., description="The approximate location where the image may have been taken"
    )
    publication_info: str = Field(..., description="Any known publication information")
    contextual_info: str = Field(
        ..., description="Any known contextual information around the image"
    )
    potential_biases: BiasAnalysis = Field(
        ..., description="A list of any potential biases present in the image"
    )
