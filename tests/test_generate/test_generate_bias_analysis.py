import unittest
from typing import List
from unittest.mock import MagicMock, patch

from image_captioning_assistant.data.data_classes import (
    BiasAnalysis,
    BiasLevel,
    BiasType,
    PotentialBias,
)
from image_captioning_assistant.generate.generate_bias_analysis import (
    generate_bias_analysis,
)


class TestGenerateBiasAnalysis(unittest.TestCase):

    @patch(
        "image_captioning_assistant.generate.generate_bias_analysis.ChatBedrockConverse"
    )
    @patch(
        "image_captioning_assistant.generate.generate_bias_analysis.format_prompt_for_nova"
    )
    def test_generate_bias_analysis_nova(self, mock_format_prompt, mock_chatbedrock):
        # Setup
        img_bytes_list = [b"image1", b"image2"]
        llm_kwargs = {"model": "nova-model", "temperature": 0.7}
        img_context = "Test context"

        mock_llm = MagicMock()
        mock_chatbedrock.return_value = mock_llm
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        expected_result = [
            PotentialBias(
                bias_type=BiasType.gender,
                bias_level=BiasLevel.low,
                explanation="Test explanation",
            )
        ]
        mock_structured_llm.invoke.return_value = expected_result

        # Execute
        result = generate_bias_analysis(img_bytes_list, llm_kwargs, img_context)

        # Assert
        mock_format_prompt.assert_called_once()
        mock_chatbedrock.assert_called_once_with(model="nova-model", temperature=0.7)
        mock_llm.with_structured_output.assert_called_once_with(BiasAnalysis)
        self.assertEqual(result, expected_result)

    @patch(
        "image_captioning_assistant.generate.generate_bias_analysis.ChatBedrockConverse"
    )
    @patch(
        "image_captioning_assistant.generate.generate_bias_analysis.format_prompt_for_claude"
    )
    def test_generate_bias_analysis_claude(self, mock_format_prompt, mock_chatbedrock):
        # Setup
        img_bytes_list = [b"image1", b"image2"]
        llm_kwargs = {"model": "claude-model", "temperature": 0.7}
        img_context = "Test context"

        mock_llm = MagicMock()
        mock_chatbedrock.return_value = mock_llm
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm

        expected_result = [
            PotentialBias(
                bias_type=BiasType.race,
                bias_level=BiasLevel.medium,
                explanation="Test explanation",
            )
        ]
        mock_structured_llm.invoke.return_value = expected_result

        # Execute
        result = generate_bias_analysis(img_bytes_list, llm_kwargs, img_context)

        # Assert
        mock_format_prompt.assert_called_once()
        mock_chatbedrock.assert_called_once_with(model="claude-model", temperature=0.7)
        mock_llm.with_structured_output.assert_called_once_with(BiasAnalysis)
        self.assertEqual(result, expected_result)

    def test_generate_bias_analysis_invalid_model(self):
        # Setup
        img_bytes_list = [b"image1"]
        llm_kwargs = {"model": "invalid-model"}
        img_context = "Test context"

        # Execute and Assert
        with self.assertRaises(ValueError):
            generate_bias_analysis(img_bytes_list, llm_kwargs, img_context)


if __name__ == "__main__":
    unittest.main()
