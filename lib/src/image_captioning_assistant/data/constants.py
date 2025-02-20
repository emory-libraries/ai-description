# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Constants for use in Metadata and Bias Determination."""

from enum import Enum


class BiasLevel(str, Enum):
    """Different levels of bias."""

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
    racial: str = "racial"
    sexual: str = "sexual"
    cultural: str = "cultural"
    ability: str = "ability"
    sexual_orientation: str = "sexual orientation"
    body_shape: str = "body shape"
    age: str = "age"
    violence: str = "violence"
    political: str = "political"
    other: str = "other"


class LibraryFormat(str, Enum):
    """Allowed format values for library materials."""

    artifact = "Artifact"
    audio = "Audio"
    cartographic = "Cartographic"
    collection = "Collection"
    dataset = "Dataset"
    digital = "Digital"
    manuscript = "Manuscript"
    mixed_material = "Mixed Material"
    moving_image = "Moving Image"
    multimedia = "Multimedia"
    notated_music = "Notated Music"
    still_image = "Still Image"
    tactile = "Tactile"
    text = "Text"
    unspecified = "Unspecified"
