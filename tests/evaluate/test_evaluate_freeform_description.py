from image_captioning_assistant.evaluate.evaluate_freeform_description import (
    FreeformResponseEvaluation,
    evaluate_freeform_response,
)


def test_evaluate_freeform_description():
    llm_freeform_description = "The picture depicts a flower in a field"
    human_freeform_description = "It's a picture of a tulip in Holland during WWII"
    freeform_description_evaluation: FreeformResponseEvaluation = (
        evaluate_freeform_response(
            llm_freeform_response=llm_freeform_description,
            human_freeform_response=human_freeform_description,
            chat_bedrock_converse_kwargs={
                "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "temperature": 0.0,
            },
        )
    )
    assert 0 <= freeform_description_evaluation.faithfulness_and_consistency <= 1
    assert 0 <= freeform_description_evaluation.completeness <= 1
    assert 0 <= freeform_description_evaluation.verbosity <= 1
    assert 0 <= freeform_description_evaluation.clarity <= 1
