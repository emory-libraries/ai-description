import unittest
from unittest.mock import MagicMock, patch

from image_captioning_assistant.data.data_classes import (
    BiasLevel,
    BiasType,
    PotentialBias,
    StructuredMetadata,
)
from image_captioning_assistant.generate.generate_structured_metadata import (
    generate_structured_metadata,
)


class TestGenerateStructuredMetadata(unittest.TestCase):

    @patch(
        "image_captioning_assistant.generate.generate_structured_metadata.ChatBedrockConverse"
    )
    def test_generate_structured_metadata_nova(self, mock_chat):
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # Create a StructuredMetadata instance with all required fields
        mock_metadata = StructuredMetadata(
            description="Test description",
            transcription="Test transcription",
            people_and_groups=["Test person"],
            date="2024-03-15",
            location="Test location",
            publication_info="Test publication info",
            contextual_info="Test contextual info",
            potential_biases=[
                PotentialBias(
                    bias_level=BiasLevel.high,
                    bias_type=BiasType.ability,
                    explanation="Explanation1",
                )
            ],
        )
        mock_structured_llm.invoke.return_value = mock_metadata

        img_bytes_list = [b"image1"]
        llm_kwargs = {"model": "anthropic.claude-3-nova-v1"}
        img_context = "Test context"

        result = generate_structured_metadata(img_bytes_list, llm_kwargs, img_context)

        self.assertIsInstance(result, StructuredMetadata)
        self.assertEqual(result.description, "Test description")
        self.assertEqual(result.transcription, "Test transcription")
        self.assertEqual(result.people_and_groups, ["Test person"])
        self.assertEqual(result.date, "2024-03-15")
        self.assertEqual(result.location, "Test location")
        self.assertEqual(result.publication_info, "Test publication info")
        self.assertEqual(result.contextual_info, "Test contextual info")
        self.assertEqual(result.potential_biases[0].bias_level, BiasLevel.high)
        self.assertEqual(result.potential_biases[0].bias_type, BiasType.ability)
        self.assertEqual(result.potential_biases[0].explanation, "Explanation1")

        mock_chat.assert_called_once_with(model="anthropic.claude-3-nova-v1")
        mock_llm.with_structured_output.assert_called_once_with(StructuredMetadata)
        mock_structured_llm.invoke.assert_called_once()

    @patch(
        "image_captioning_assistant.generate.generate_structured_metadata.ChatBedrockConverse"
    )
    def test_generate_structured_metadata_claude(self, mock_chat):
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        # Create a StructuredMetadata instance with all required fields
        mock_metadata = StructuredMetadata(
            description="Test description",
            transcription="Test transcription",
            people_and_groups=["Test person"],
            date="2024-03-15",
            location="Test location",
            publication_info="Test publication info",
            contextual_info="Test contextual info",
            potential_biases=[
                PotentialBias(
                    bias_level=BiasLevel.high,
                    bias_type=BiasType.ability,
                    explanation="Explanation1",
                )
            ],
        )
        mock_structured_llm.invoke.return_value = mock_metadata

        img_bytes_list = [b"image1"]
        llm_kwargs = {"model": "anthropic.claude-3-sonnet-20240229-v1:0"}
        img_context = "Test context"

        result = generate_structured_metadata(img_bytes_list, llm_kwargs, img_context)

        self.assertIsInstance(result, StructuredMetadata)
        self.assertEqual(result.description, "Test description")
        self.assertEqual(result.transcription, "Test transcription")
        self.assertEqual(result.people_and_groups, ["Test person"])
        self.assertEqual(result.date, "2024-03-15")
        self.assertEqual(result.location, "Test location")
        self.assertEqual(result.potential_biases[0].bias_level, BiasLevel.high)
        self.assertEqual(result.potential_biases[0].bias_type, BiasType.ability)
        self.assertEqual(result.potential_biases[0].explanation, "Explanation1")

        mock_chat.assert_called_once_with(
            model="anthropic.claude-3-sonnet-20240229-v1:0"
        )
        mock_llm.with_structured_output.assert_called_once_with(StructuredMetadata)
        mock_structured_llm.invoke.assert_called_once()

    def test_generate_structured_metadata_invalid_model(self):
        img_bytes_list = [b"image1"]
        llm_kwargs = {"model": "invalid_model"}
        img_context = "Test context"

        with self.assertRaises(ValueError):
            generate_structured_metadata(img_bytes_list, llm_kwargs, img_context)


if __name__ == "__main__":
    unittest.main()
