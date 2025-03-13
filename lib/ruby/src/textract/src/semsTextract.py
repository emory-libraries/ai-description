# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

"""Textract extractor."""

import asyncio
import os
import time
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, List, Optional, Set

import pandas as pd
from loguru import logger
from pdf2image import convert_from_bytes
from PIL import Image

from .client import S3Manager, TextractManager
from .ingestConfig import ingest_config, IngestConfig
from .utils import get_paginated_results


class TextractExtractor:
    """Handles OCR processing using AWS Textract."""

    def __init__(self, config: IngestConfig = ingest_config) -> None:
        """Initialize the Textract extractor."""
        logger.debug(f"Initializing {self.__class__.__name__}")
        self.config = config
        logger.debug(f"{self.__class__.__name__} initialized successfully")

    def _extract_page_images(self, *, blocks: List[Dict], original_image: Image.Image) -> List[Image.Image]:
        """Extract images from a single page or image."""
        logger.debug("Starting image extraction from page")
        try:
            width, height = original_image.size
            logger.debug(f"Original image dimensions: {width}x{height}")
        except Exception as e:
            logger.error("Error getting image dimensions: {error}", error=str(e))
            return []

        images = []
        for block in blocks:
            try:
                cropped = self._crop_image(block, original_image, width, height)
                if cropped:
                    images.append(cropped)
            except Exception as e:
                logger.error("Error cropping image from block: {error}", error=str(e))
                continue

        logger.debug(f"Extracted {len(images)} images from page")
        return images

    def _extract_images(
        self, *, blocks: List[Dict], document_bytes: bytes, is_pdf: bool
    ) -> Dict[int, List[Image.Image]]:
        """Extract images organized by page number."""
        logger.info("Starting image extraction from document")
        try:
            filter_result = self._filter_images(blocks)
            filtered_blocks = filter_result["filtered_blocks"]
            pages_to_process = filter_result["pages"]

            if not filtered_blocks:
                logger.debug("No image blocks found to process")
                return {}

            logger.debug(f"Found {len(filtered_blocks)} pages with images to process")
            images_by_page = defaultdict(list)

            if is_pdf:
                logger.debug("Processing PDF document")
                page_images = self._convert_pdf_pages(document_bytes=document_bytes, pages=list(pages_to_process))

                for page_num, page_image in page_images.items():
                    if page_num in filtered_blocks:
                        logger.debug(f"Processing images on page {page_num}")
                        extracted = self._extract_page_images(
                            blocks=filtered_blocks[page_num], original_image=page_image
                        )
                        images_by_page[page_num].extend(extracted)
            else:
                logger.debug("Processing single image document")
                original_image = Image.open(BytesIO(document_bytes))
                images = self._extract_page_images(blocks=blocks, original_image=original_image)
                images_by_page[1].extend(images)

            logger.info(f"Successfully extracted images from {len(images_by_page)} pages")
            return dict(images_by_page)

        except Exception as e:
            logger.error("Error extracting images: {error}", error=str(e))
            return {}

    def _extract_words(self, blocks: List[Dict]) -> List[Dict[str, Any]]:
        """Extract words."""
        logger.debug("Starting word extraction from blocks")
        words = []

        for block in blocks:
            if block["BlockType"] == "WORD":
                words.append(
                    {
                        "text": block["Text"],
                        "page_number": block["Page"],
                        "confidence": block.get("Confidence", 0.0),
                    }
                )

        logger.debug(f"Extracted {len(words)} words")
        return words

    def _extract_text(self, blocks: List[Dict]) -> Dict[int, Dict[str, Any]]:
        """Extract text content and confidence scores organized by page number."""
        logger.debug("Starting text extraction from blocks")
        text_by_page = defaultdict(lambda: {"text": [], "confidence": []})

        for block in blocks:
            if block["BlockType"] in ["LINE", "WORD"] and "Text" in block:
                page = block["Page"]
                text_by_page[page]["text"].append(block["Text"])
                text_by_page[page]["confidence"].append(block.get("Confidence", 0.0))

        result = {}
        for page, data in text_by_page.items():
            avg_confidence = sum(data["confidence"]) / len(data["confidence"]) if data["confidence"] else 0.0
            result[page] = {
                "text": " ".join(data["text"]),
                "quality_score": avg_confidence,
            }

        logger.debug(f"Extracted text and confidence scores from {len(result)} pages")
        return result

    def _extract_tables(self, blocks: List[Dict]) -> Dict[int, List[pd.DataFrame]]:
        """Extract tables organized by page number."""
        logger.debug("Starting table extraction from blocks")
        tables_by_page = defaultdict(list)
        table_cells = defaultdict(list)

        current_table = None
        for block in blocks:
            if block["BlockType"] == "TABLE":
                current_table = block["Id"]
                logger.debug(f"Found new table with ID: {current_table}")
            elif block["BlockType"] == "CELL" and current_table:
                if "Relationships" in block:
                    cell_text = self._get_text_from_cell(blocks, block["Id"])
                    table_cells[(block["Page"], current_table)].append(
                        {"text": cell_text, "row": block["RowIndex"], "col": block["ColumnIndex"]}
                    )

        for (page, _), cells in table_cells.items():
            if cells:
                logger.debug(f"Converting table cells to DataFrame for page {page}")
                df = pd.DataFrame(cells)
                df = df.pivot(index="row", columns="col", values="text")
                tables_by_page[page].append(df)

        result = dict(tables_by_page)
        logger.debug(f"Extracted {sum(len(tables) for tables in result.values())} tables from {len(result)} pages")
        return result

    def _crop_image(self, block: Dict, original_image: Image.Image, width: int, height: int) -> Optional[Image.Image]:
        """Crop an image based on the bounding box coordinates from a Textract block."""
        try:
            bbox = block["Geometry"]["BoundingBox"]
            logger.debug(f"Cropping image with bounding box: {bbox}")

            crop_high = 1.1
            crop_down = 0.9

            left = max(0, float(bbox["Left"] * crop_down * width))
            top = max(0, float(bbox["Top"] * crop_down * height))
            right = min(width, float(((bbox["Left"] + bbox["Width"]) * crop_high) * width))
            bottom = min(height, float(((bbox["Top"] + bbox["Height"]) * crop_high) * height))

            logger.debug(f"Calculated crop coordinates: left={left}, top={top}, right={right}, bottom={bottom}")
            return original_image.crop((left, top, right, bottom))

        except Exception as e:
            logger.error("Error cropping image: {error}", error=str(e))
            return None

    def _get_text_from_cell(self, blocks: List[Dict], cell_id: str) -> str:
        """Extract text from a specific cell."""
        cell_block = next((block for block in blocks if block["Id"] == cell_id), None)
        if not cell_block or "Relationships" not in cell_block:
            logger.debug(f"No text found for cell {cell_id}")
            return ""

        words = [word for rel in cell_block["Relationships"] if rel["Type"] == "CHILD" for word in rel["Ids"]]
        word_blocks = [block for block in blocks if block["Id"] in words]
        text = " ".join(word_block["Text"] for word_block in word_blocks if "Text" in word_block)
        logger.debug(f"Extracted text from cell {cell_id}: {text[:50]}...")
        return text

    def _filter_images(self, blocks: List[Dict]) -> Dict[str, Any]:
        """Filter out small images and return significant ones."""
        logger.debug("Filtering image blocks")
        filtered_output = defaultdict(list)
        pages = set()

        for block in blocks:
            if (
                block["BlockType"] == "LAYOUT_FIGURE"
                and block["Geometry"]["BoundingBox"]["Width"] > 0.15
                and block["Geometry"]["BoundingBox"]["Height"] > 0.15
            ):
                page = block["Page"]
                filtered_output[page].append(block)
                pages.add(page)

        logger.debug(f"Found {len(pages)} pages with significant images")
        return {"filtered_blocks": dict(filtered_output), "pages": pages}

    def _convert_pdf_pages(self, document_bytes: bytes, pages: Optional[List[int]] = None) -> Dict[int, Image.Image]:
        """Convert PDF pages to images."""
        logger.debug(f"Converting PDF pages: {pages if pages else 'all'}")
        try:
            if pages:
                images = convert_from_bytes(document_bytes, first_page=min(pages), last_page=max(pages))
                result = {page: image for page, image in enumerate(images, start=min(pages)) if page in pages}
            else:
                images = convert_from_bytes(document_bytes)
                result = {i + 1: image for i, image in enumerate(images)}

            logger.debug(f"Successfully converted {len(result)} PDF pages to images")
            return result

        except Exception as e:
            logger.error("Error converting PDF pages: {error}", error=str(e))
            return {}

    def _pages_to_bytes(self, document_bytes: bytes, is_pdf: bool, pages_with_content: List[int]) -> Dict[int, bytes]:
        """Convert only pages with tables or images to bytes object."""
        logger.debug(f"Converting {len(pages_with_content)} pages to bytes")
        pages_bytes = {}

        try:
            if is_pdf:
                if not pages_with_content:
                    logger.debug("No pages with content to convert")
                    return {}

                page_images = self._convert_pdf_pages(document_bytes=document_bytes, pages=pages_with_content)
                for page_num, image in page_images.items():
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format="PNG")
                    pages_bytes[page_num] = img_byte_arr.getvalue()
                    logger.debug(f"Converted page {page_num} to bytes")
            else:
                if 1 in pages_with_content:
                    pages_bytes[1] = document_bytes
                    logger.debug("Converted single image to bytes")

            logger.debug(f"Successfully converted {len(pages_bytes)} pages to bytes")
            return pages_bytes

        except Exception as e:
            logger.error("Error converting pages to bytes: {error}", error=str(e))
            return {}

    async def _call_textract(self, *, bucket: str, key: str) -> Dict[str, Any]:
        """Process document with Textract."""
        start_time = time.time()
        logger.info(f"Starting Textract processing for s3://{bucket}/{key}")

        textract_manager = TextractManager()
        await textract_manager.start()
        textract_client = textract_manager.client

        try:
            initial_params = {
                "DocumentLocation": {"S3Object": {"Bucket": bucket, "Name": key}},
                "FeatureTypes": self.config.processing.textract_feature_types,
                "OutputConfig": {
                    "S3Bucket": self.config.storage.textract_bucket_name,
                    "S3Prefix": f"results/{os.path.basename(key)}",
                },
            }
            logger.debug(f"Textract parameters: {initial_params}")

            response = await textract_client.start_document_analysis(**initial_params)
            job_id = response["JobId"]
            logger.info(f"Started Textract job: {job_id}")

            polling_start = time.time()
            poll_count = 0
            while True:
                poll_count += 1
                elapsed_time = time.time() - polling_start

                check_job_response = await textract_client.get_document_analysis(JobId=job_id)
                status = check_job_response["JobStatus"]
                logger.debug(f"Poll #{poll_count}: Status={status}, Elapsed time={elapsed_time:.2f} seconds")

                if status in ["SUCCEEDED", "PARTIAL_SUCCESS"]:
                    logger.info(f"Job completed successfully after {poll_count} polls ({elapsed_time:.2f} seconds)")
                    break
                elif status == "FAILED":
                    message = check_job_response.get("StatusMessage", "Unknown error")
                    logger.error(f"Textract job failed: {message}")
                    raise Exception(f"Textract job failed: {message}")
                elif elapsed_time > self.config.processing.max_polling_time:
                    logger.error(f"Textract job timed out after {elapsed_time:.2f} seconds")
                    raise TimeoutError(f"Textract job timed out for document s3://{bucket}/{key}")

                await asyncio.sleep(10)

            logger.debug("Retrieving paginated results")
            results = await get_paginated_results(
                client=textract_client,
                method="get_document_analysis",
                initial_params={"JobId": job_id},
                result_key="Blocks",
            )

            total_time = time.time() - start_time
            logger.info(f"Textract processing completed in {total_time:.2f} seconds")
            return results

        except Exception as e:
            logger.error("Error in Textract processing: {error}", error=str(e))
            raise

        finally:
            await textract_manager.stop()

    async def extract(self, *, bucket: str, key: str) -> Dict[str, Any]:
        """Process document using Textract and extract text, tables, and images."""
        process_start = time.time()
        logger.info(f"Starting document extraction for s3://{bucket}/{key}")

        s3_manager = S3Manager()
        await s3_manager.start()
        s3_client = s3_manager.client

        try:
            is_pdf = key.lower().endswith(".pdf")
            logger.debug(f"Document type: {'PDF' if is_pdf else 'Image'}")

            textract_response = await self._call_textract(bucket=bucket, key=key)
            num_pages = textract_response["DocumentMetadata"]["Pages"]
            blocks = textract_response["Blocks"]
            logger.info(f"Document analysis complete: {num_pages} pages, {len(blocks)} blocks detected")

            response = await s3_client.get_object(Bucket=bucket, Key=key)
            document_bytes = await response["Body"].read()
            logger.debug(f"Downloaded document size: {len(document_bytes)} bytes")

            words = self._extract_words(blocks)
            logger.debug(f"Extracted {len(words)} words")

            text = self._extract_text(blocks)
            logger.debug(f"Extracted text from {len(text)} pages")

            # tables = self._extract_tables(blocks)
            # logger.debug(f"Extracted {sum(len(tables) for tables in tables.values())} tables")

            images = self._extract_images(blocks=blocks, document_bytes=document_bytes, is_pdf=is_pdf)
            logger.debug(f"Extracted images from {len(images)} pages")

            pages_with_content_set: Set[int] = set()
            # pages_with_content_set.update(tables.keys())
            pages_with_content_set.update(images.keys())
            pages_with_content = sorted(pages_with_content_set)

            page_bytes = self._pages_to_bytes(
                document_bytes=document_bytes,
                is_pdf=is_pdf,
                pages_with_content=pages_with_content,
            )
            logger.debug(f"Converted {len(page_bytes)} pages to bytes")

            total_time = time.time() - process_start
            logger.info(f"Document extraction completed in {total_time:.2f} seconds")

            return {
                "words": words,
                "text": text,
                "images": images,
                "page_bytes": page_bytes,
            }

        except Exception as e:
            logger.error("Error in document extraction: {error}", error=str(e))
            raise

        finally:
            await s3_manager.stop()
