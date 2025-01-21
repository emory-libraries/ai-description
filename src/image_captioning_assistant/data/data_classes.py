"""Data classes used throughout the metadata generation process."""

from enum import Enum

from pydantic import BaseModel


class BiasLevel(str, Enum):
    """Different levels of bias."""

    none: str = "None detected"
    # Low potential for harm: unintentional exclusion; gaps or imbalances in the
    # representation of individuals and communities
    low: str = "Low potential for harm"
    # Medium potential for harm: use of obsolete language terms; potential stereotyping that is a
    # result of the historical time period
    medium: str = "Medium potential for harm"
    # High potential for harm: use of offensive terminology, clearly identified
    # racist/sexist/etc. stereotypes and tropes; images of violence or abuse
    high: str = "High potential for harm"


class BiasType(str, Enum):
    """Different types of bias."""

    gender: str = "gender"
    racial: str = "racial"
    cultural: str = "cultural"
    ableist: str = "ableist"
    other: str = "other"


class BiasAnalysis(BaseModel):
    """Potential bias present in an image."""

    bias_type: BiasType
    bias_level: BiasLevel
    comments: str


class StructuredMetadata(BaseModel):
    """Metadata fields for an image.

    This is the metadata requested for items in the Langmuir collection.
    """

    description: str
    transcription: str
    names: list[str]
    date: str
    location: str
    publication_info: str
    contextual_info: str
    bias_analysis: BiasAnalysis
