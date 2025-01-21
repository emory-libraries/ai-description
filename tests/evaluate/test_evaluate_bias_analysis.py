from unittest.mock import Mock, patch

from image_captioning_assistant.data.data_classes import (
    BiasAnalysis,
    BiasLevel,
    BiasType,
)
from image_captioning_assistant.evaluate.evaluate_bias_analysis import (
    BiasAnalysisEvaluation,
    FreeformResponseEvaluation,
    evaluate_bias_analysis,
)


@patch(
    "image_captioning_assistant.evaluate.evaluate_bias_analysis.evaluate_freeform_response"
)
def test_evaluate_structured_metadata(mock_evaluate_freeform_response):
    # Define the expected output
    expected_evaluation = FreeformResponseEvaluation(
        faithfulness_and_consistency=1.0, completeness=0.0, verbosity=0.0, clarity=1.0
    )
    mock_evaluate_freeform_response.return_value = expected_evaluation

    llm_bias_analysis = BiasAnalysis(
        bias_type=BiasType.racial,
        bias_level=BiasLevel.high,
        comments="Water fountain and a sign above it that says 'whites'",
    )
    human_bias_analysis = BiasAnalysis(
        bias_type=BiasType.racial,
        bias_level=BiasLevel.high,
        comments="A water fountain and a sign above it tha reads 'whites'",
    )
    bias_analysis_evaluation: BiasAnalysisEvaluation = evaluate_bias_analysis(
        llm_bias_analysis=llm_bias_analysis,
        human_bias_analysis=human_bias_analysis,
        chat_bedrock_converse_kwargs={
            "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "temperature": 0.0,
        },
    )
    mock_evaluate_freeform_response.assert_called_once()
    assert 0 <= bias_analysis_evaluation.bias_type_match <= 1
    assert 0 <= bias_analysis_evaluation.bias_level_match <= 1
    assert (
        0
        <= bias_analysis_evaluation.comments_evaluation.faithfulness_and_consistency
        <= 1
    )
    assert 0 <= bias_analysis_evaluation.comments_evaluation.completeness <= 1
    assert 0 <= bias_analysis_evaluation.comments_evaluation.verbosity <= 1
    assert 0 <= bias_analysis_evaluation.comments_evaluation.clarity <= 1
