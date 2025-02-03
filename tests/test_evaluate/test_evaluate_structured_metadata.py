import unittest
from unittest.mock import MagicMock, patch

from image_captioning_assistant.data.data_classes import (
    BiasLevel,
    BiasType,
    PotentialBias,
    StructuredMetadata,
)
from image_captioning_assistant.evaluate.evaluate_structured_metadata import (
    BiasAnalysisEvaluation,
    FreeformResponseEvaluation,
    PartialStructuredMetadataEvaluation,
    StructuredMetadataEvaluation,
    evaluate_structured_metadata,
)


class TestEvaluateStructuredMetadata(unittest.TestCase):

    @patch(
        "image_captioning_assistant.evaluate.evaluate_structured_metadata.evaluate_freeform_response"
    )
    @patch(
        "image_captioning_assistant.evaluate.evaluate_structured_metadata.evaluate_potential_biases"
    )
    @patch(
        "image_captioning_assistant.evaluate.evaluate_structured_metadata.ChatBedrockConverse"
    )
    def test_evaluate_structured_metadata(
        self, mock_chat_bedrock, mock_evaluate_bias, mock_evaluate_freeform
    ):
        # Mock the evaluate_freeform_response function
        mock_evaluate_freeform.return_value = FreeformResponseEvaluation(
            faithfulness_and_consistency=0.9,
            completeness=0.8,
            verbosity=0.7,
            clarity=0.6,
        )

        # Mock the evaluate_bias_analysis function
        mock_evaluate_bias.return_value = BiasAnalysisEvaluation(
            bias_type_alignment=0.8,
            bias_level_alignment=0.7,
            explanation_alignment=0.5,
        )

        # Mock the ChatBedrockConverse.invoke method
        mock_invoke = MagicMock()
        mock_invoke.return_value = PartialStructuredMetadataEvaluation(
            transcription_evaluation=0.9,
            names_evaluation=0.8,
            date_evaluation=0.7,
            location_evaluation=0.6,
            publication_info_evaluation=0.5,
            contextual_info_evaluation=0.4,
        )
        mock_chat_bedrock.return_value.with_structured_output.return_value.invoke = (
            mock_invoke
        )

        # Create sample input data
        llm_bias_analysis = PotentialBias(
            bias_type=BiasType.ability,
            bias_level=BiasLevel.high,
            explanation="LLM Comment",
        )
        llm_metadata = StructuredMetadata(
            description="LLM description",
            transcription="LLM transcription",
            people_and_groups=["LLM Name 1", "LLM Name 2"],
            date="2023-01-01",
            location="LLM Location",
            publication_info="LLM Publication Info",
            contextual_info="LLM Contextual Info",
            potential_biases=[llm_bias_analysis],
        )
        human_bias_analysis = PotentialBias(
            bias_type=BiasType.ability,
            bias_level=BiasLevel.high,
            explanation="Human comment",
        )
        human_metadata = StructuredMetadata(
            description="Human description",
            transcription="Human transcription",
            people_and_groups=["Human Name 1", "Human Name 2"],
            date="2023-01-01",
            location="Human Location",
            publication_info="Human Publication Info",
            contextual_info="Human Contextual Info",
            potential_biases=[human_bias_analysis],
        )

        chat_bedrock_kwargs = {"model": "anthropic.claude-3-5-sonnet-20240620-v1:0"}

        # Call the function
        result = evaluate_structured_metadata(
            llm_metadata, human_metadata, chat_bedrock_kwargs
        )

        # Assert the result
        self.assertIsInstance(result, StructuredMetadataEvaluation)
        self.assertEqual(result.transcription_evaluation, 0.9)
        self.assertEqual(result.names_evaluation, 0.8)
        self.assertEqual(result.date_evaluation, 0.7)
        self.assertEqual(result.location_evaluation, 0.6)
        self.assertEqual(result.publication_info_evaluation, 0.5)
        self.assertEqual(result.contextual_info_evaluation, 0.4)

        self.assertEqual(
            result.description_evaluation.faithfulness_and_consistency, 0.9
        )
        self.assertEqual(result.description_evaluation.completeness, 0.8)
        self.assertEqual(result.description_evaluation.verbosity, 0.7)
        self.assertEqual(result.description_evaluation.clarity, 0.6)

        self.assertEqual(result.bias_analysis_evaluation.bias_type_alignment, 0.8)
        self.assertEqual(result.bias_analysis_evaluation.bias_level_alignment, 0.7)
        self.assertEqual(result.bias_analysis_evaluation.explanation_alignment, 0.5)

        # Assert that the mocked functions were called with correct arguments
        mock_evaluate_freeform.assert_called_once_with(
            llm_freeform_response="LLM description",
            human_freeform_response="Human description",
            chat_bedrock_converse_kwargs=chat_bedrock_kwargs,
        )

        mock_evaluate_bias.assert_called_once_with(
            llm_potential_biases=[llm_bias_analysis],
            human_potential_biases=[human_bias_analysis],
            chat_bedrock_converse_kwargs=chat_bedrock_kwargs,
        )
        mock_chat_bedrock.assert_called_once_with(**chat_bedrock_kwargs)
        mock_invoke.assert_called_once()
