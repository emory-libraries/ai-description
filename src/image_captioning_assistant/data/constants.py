from enum import Enum


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
