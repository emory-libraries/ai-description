from image_captioning_assistant.data.data_classes import (
    BiasAnalysis,
    BiasLevel,
    BiasType,
)
from image_captioning_assistant.evaluate.evaluate_bias_analysis import (
    BiasAnalysisEvaluation,
    evaluate_bias_analysis,
)


def test_evaluate_structured_metadata():
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
