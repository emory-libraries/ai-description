from image_captioning_assistant.data.data_classes import (
    BiasAnalysis,
    BiasLevel,
    BiasType,
    StructuredMetadata,
)
from image_captioning_assistant.evaluate.evaluate_structured_metadata import (
    StructuredMetadataEvaluation,
    evaluate_structured_metadata,
)


def test_evaluate_structured_metadata():
    llm_bias_analysis = BiasAnalysis(
        bias_type=BiasType.other,
        bias_level=BiasLevel.none,
        comments="No bias could be identified",
    )
    llm_structured_metadata = StructuredMetadata(
        description="The picture depicts a flower in a field",
        transcription="I like flowers",
        names=[],
        date="1950-01-01",
        location="Field, maybe Holland",
        publication_info="Published by the New York Times",
        contextual_info="Could be during WWII",
        bias_analysis=llm_bias_analysis,
    )
    human_bias_analysis = BiasAnalysis(
        bias_type=BiasType.other,
        bias_level=BiasLevel.none,
        comments="I didn't notice anything",
    )
    human_structured_metadata = StructuredMetadata(
        description="It's flower in a meadow",
        transcription="I like flowers",
        names=[],
        date="1950-01-01",
        location="St. Paul, Minnesota",
        publication_info="Penguin Publishing",
        contextual_info="This was Jimmy Carter's farm",
        bias_analysis=human_bias_analysis,
    )
    structured_metadata_evaluation: StructuredMetadataEvaluation = (
        evaluate_structured_metadata(
            llm_structured_metadata=llm_structured_metadata,
            human_structured_metadata=human_structured_metadata,
            chat_bedrock_converse_kwargs={
                "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "temperature": 0.0,
            },
        )
    )
    # Evaluate description
    assert (
        0
        <= structured_metadata_evaluation.description_evaluation.faithfulness_and_consistency
        <= 1
    )
    assert 0 <= structured_metadata_evaluation.description_evaluation.completeness <= 1
    assert 0 <= structured_metadata_evaluation.description_evaluation.verbosity <= 1
    assert 0 <= structured_metadata_evaluation.description_evaluation.clarity <= 1
    # Evaluate transcription
    assert 0 <= structured_metadata_evaluation.transcription_evaluation <= 1
    # Evaluate names
    assert 0 <= structured_metadata_evaluation.names_evaluation <= 1
    # Evaluate dates
    assert 0 <= structured_metadata_evaluation.dates_evaluation <= 1
    # Evaluate location
    assert 0 <= structured_metadata_evaluation.location_evaluation <= 1
    # Evaluate publication_info
    assert 0 <= structured_metadata_evaluation.publication_info_evaluation <= 1
    # Evaluate contextual_info
    assert 0 <= structured_metadata_evaluation.contextual_info_evaluation <= 1
    # Evaluate bias
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.bias_type_match
        <= 1
    )
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.bias_level_match
        <= 1
    )
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.comments_evaluation.faithfulness_and_consistency
        <= 1
    )
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.comments_evaluation.completeness
        <= 1
    )
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.comments_evaluation.verbosity
        <= 1
    )
    assert (
        0
        <= structured_metadata_evaluation.bias_analysis_evaluation.comments_evaluation.clarity
        <= 1
    )
