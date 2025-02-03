import unittest
from unittest.mock import Mock, patch

from image_captioning_assistant.evaluate.evaluate_freeform_description import (
    FreeformResponseEvaluation,
    evaluate_freeform_response,
)


class TestEvaluateStructuredMetadata(unittest.TestCase):

    @patch(
        "image_captioning_assistant.evaluate.evaluate_freeform_description.ChatBedrockConverse"
    )
    def test_evaluate_freeform_description(self, mock_chat_bedrock):
        # Set up the mock
        mock_structured_llm = Mock()
        mock_chat_bedrock.return_value.with_structured_output.return_value = (
            mock_structured_llm
        )

        # Define the expected output
        expected_evaluation = FreeformResponseEvaluation(
            faithfulness_and_consistency=1.0,
            completeness=0.0,
            verbosity=0.0,
            clarity=1.0,
        )
        mock_structured_llm.invoke.return_value = expected_evaluation

        # Call the function
        freeform_description_evaluation = evaluate_freeform_response(
            llm_freeform_response="The picture depicts a flower in a field",
            human_freeform_response="It's a picture of a tulip in Holland during WWII",
            chat_bedrock_converse_kwargs={
                "model": "anthropic.claude-3-5-sonnet-20240620-v1:0",
                "temperature": 0.0,
            },
        )

        # Verify that the mock was called correctly
        mock_chat_bedrock.assert_called_once_with(
            model="anthropic.claude-3-5-sonnet-20240620-v1:0", temperature=0.0
        )
        mock_chat_bedrock.return_value.with_structured_output.assert_called_once_with(
            FreeformResponseEvaluation
        )
        mock_structured_llm.invoke.assert_called_once()

        # Assertions
        self.assertEqual(freeform_description_evaluation, expected_evaluation)
