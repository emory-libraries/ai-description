import unittest
from unittest.mock import Mock, patch

from image_captioning_assistant.data.data_classes import (
    BiasLevel,
    BiasType,
    PotentialBias,
)
from image_captioning_assistant.evaluate.evaluate_bias_analysis import (
    BiasAnalysisEvaluation,
    evaluate_potential_biases,
)


class TestEvaluateBiasAnalysis(unittest.TestCase):

    @patch(
        "image_captioning_assistant.evaluate.evaluate_bias_analysis.ChatBedrockConverse"
    )
    def test_evaluate_structured_metadata(self, mock_chat_bedrock):
        # Set up the mock
        mock_structured_llm = Mock()
        mock_chat_bedrock.return_value.with_structured_output.return_value = (
            mock_structured_llm
        )
        expected_evaluation = BiasAnalysisEvaluation(
            bias_level_alignment=1.0,
            bias_type_alignment=0.3,
            explanation_alignment=0.4,
        )
        mock_structured_llm.invoke.return_value = expected_evaluation
        llm_bias_analysis = PotentialBias(
            bias_type=BiasType.race,
            bias_level=BiasLevel.high,
            explanation="Water fountain and a sign above it that says 'whites'",
        )
        human_bias_analysis = PotentialBias(
            bias_type=BiasType.race,
            bias_level=BiasLevel.high,
            explanation="A water fountain and a sign above it tha reads 'whites'",
        )
        potential_bias_evaluation = evaluate_potential_biases(
            llm_potential_biases=[llm_bias_analysis],
            human_potential_biases=[human_bias_analysis],
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
            BiasAnalysisEvaluation
        )
        mock_structured_llm.invoke.assert_called_once()

        # Assertions
        self.assertEqual(potential_bias_evaluation, expected_evaluation)
