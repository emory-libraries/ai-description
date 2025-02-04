import unittest
from unittest.mock import MagicMock, patch

from image_captioning_assistant.data.data_classes import PotentialBias
from image_captioning_assistant.data.db.database_manager import DatabaseManager
from image_captioning_assistant.generate.generate_structured_metadata import (
    StructuredMetadata,
)
from image_captioning_assistant.orchestrate.process_job import process_job


class TestProcessJob(unittest.TestCase):

    def setUp(self):
        self.db_manager = MagicMock(spec=DatabaseManager)
        self.db_manager.put_document = MagicMock()
        self.s3_bucket = "test-bucket"
        self.s3_prefix = "test-prefix"
        self.batch_job_name = "test-job"
        self.aws_region = "us-west-2"

    @patch("image_captioning_assistant.orchestrate.process_job.list_contents_of_folder")
    @patch("image_captioning_assistant.orchestrate.process_job.load_image_bytes")
    @patch(
        "image_captioning_assistant.orchestrate.process_job.generate_structured_metadata"
    )
    @patch(
        "image_captioning_assistant.orchestrate.process_job.get_document_metadata_by_id_and_job"
    )
    @patch(
        "image_captioning_assistant.orchestrate.process_job.delete_document_metadata_by_id_and_job"
    )
    @patch(
        "image_captioning_assistant.orchestrate.process_job.clear_document_bias_by_job_and_document"
    )
    @patch("image_captioning_assistant.orchestrate.process_job.put_document")
    @patch("image_captioning_assistant.orchestrate.process_job.create_document_bias")
    @patch(
        "image_captioning_assistant.orchestrate.process_job.create_document_metadata"
    )
    def test_process_job_normal_flow(
        self,
        mock_create_metadata,
        mock_create_bias,
        mock_put_document,
        mock_clear_bias,
        mock_delete_metadata,
        mock_get_metadata,
        mock_generate_metadata,
        mock_load_image,
        mock_list_contents,
    ):
        # Setup
        mock_list_contents.return_value = ["image1.jpg", "image2.jpg"]
        mock_load_image.return_value = b"fake_image_bytes"
        mock_get_metadata.return_value = None
        mock_generate_metadata.return_value = StructuredMetadata(
            description="Test description",
            transcription="Test transcription",
            people_and_groups=["Person A", "Group B"],
            date="2023-01-01",
            location="Test Location",
            publication_info="Test Publication",
            contextual_info="Test Context",
            potential_biases=[
                PotentialBias(
                    bias_type="gender",
                    bias_level="low",
                    explanation="Test Explanation",
                )
            ],
        )

        # Execute
        process_job(
            batch_job_name=self.batch_job_name,
            s3_bucket=self.s3_bucket,
            s3_prefix=self.s3_prefix,
            db_manager=self.db_manager,
            aws_region=self.aws_region,
        )

        # Assert
        self.assertEqual(mock_put_document.call_count, 2)
        self.assertEqual(mock_create_bias.call_count, 2)
        self.assertEqual(mock_create_metadata.call_count, 2)
        mock_delete_metadata.assert_not_called()
        mock_clear_bias.assert_not_called()

    @patch("image_captioning_assistant.orchestrate.process_job.list_contents_of_folder")
    @patch(
        "image_captioning_assistant.orchestrate.process_job.get_document_metadata_by_id_and_job"
    )
    def test_process_job_skip_completed(self, mock_get_metadata, mock_list_contents):
        # Setup
        mock_list_contents.return_value = ["image1.jpg"]
        mock_get_metadata.return_value = MagicMock()  # Simulating existing metadata

        # Execute
        process_job(
            self.batch_job_name,
            self.s3_bucket,
            self.s3_prefix,
            self.db_manager,
            self.aws_region,
            skip_completed=True,
        )

        # Assert
        mock_get_metadata.assert_called_once()
        # Ensure no further processing occurred
        self.db_manager.put_document.assert_not_called()

    @patch("image_captioning_assistant.orchestrate.process_job.list_contents_of_folder")
    @patch("image_captioning_assistant.orchestrate.process_job.load_image_bytes")
    @patch(
        "image_captioning_assistant.orchestrate.process_job.generate_structured_metadata"
    )
    def test_process_job_exception_handling(
        self, mock_generate_metadata, mock_load_image, mock_list_contents
    ):
        # Setup
        mock_list_contents.return_value = ["image1.jpg"]
        mock_load_image.side_effect = Exception("Test exception")

        # Execute
        process_job(
            self.batch_job_name,
            self.s3_bucket,
            self.s3_prefix,
            self.db_manager,
            self.aws_region,
        )

        # Assert
        mock_load_image.assert_called_once()
        mock_generate_metadata.assert_not_called()  # Ensure processing stopped after exception


if __name__ == "__main__":
    unittest.main()
