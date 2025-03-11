/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import { Container, Header, Textarea, SpaceBetween, Box } from '@cloudscape-design/components';
import { useMetadataContext } from '../MetadataContext';

function MetadataSection({ fieldKey, fieldValue }) {
  const { handleMetadataEdit } = useMetadataContext();

  // Skip certain fields from being displayed
  if (
    [
      'job_type',
      'job_name',
      'work_id',
      'work_status',
      'image_s3_uris',
      'context_s3_uri',
      'original_metadata_s3_uri',
      'image_presigned_urls',
      'metadata_biases',
    ].includes(fieldKey)
  ) {
    return null;
  }

  // Format the field key for display
  const formattedKey = fieldKey.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());

  // Special handling for fields
  const isTranscription = fieldKey === 'transcription';
  const isPageBiases = fieldKey === 'page_biases';

  // Extract rationale and prepare editable value
  let rationale = null;
  let editableValue = fieldValue;

  // Handle transcription's special structure
  if (isTranscription && fieldValue && typeof fieldValue === 'object') {
    if ('model_notes' in fieldValue) {
      rationale = fieldValue.model_notes;
    }

    // If transcriptions field exists, use it as the editable value
    if ('transcriptions' in fieldValue) {
      editableValue = fieldValue.transcriptions;
    } else {
      // Otherwise use the whole object except model_notes
      const { model_notes, ...rest } = fieldValue;
      editableValue = rest;
    }
  }
  // Handle standard explanation/value pattern
  else if (fieldValue && typeof fieldValue === 'object' && 'explanation' in fieldValue && 'value' in fieldValue) {
    rationale = fieldValue.explanation;
    editableValue = fieldValue.value;
  }

  // Determine if the value is a list
  const isList = Array.isArray(editableValue) && !isTranscription && !isPageBiases;

  // Format the value for display
  let stringValue;

  // Format transcription field
  if (isTranscription && Array.isArray(editableValue)) {
    let formatted = '';

    editableValue.forEach((page, i) => {
      // Add page number for multi-page transcriptions
      if (i > 0) {
        formatted += "\n\n--- PAGE " + (i + 1) + " ---\n\n";
      } else if (editableValue.length > 1) {
        formatted += "--- PAGE 1 ---\n\n";
      }

      // Format handwriting section
      if (page.handwriting && page.handwriting.length > 0) {
        formatted += "HANDWRITING:\n";
        formatted += page.handwriting.join("\n");
      }

      // Add separator between sections if both exist
      if (page.handwriting?.length > 0 && page.printed_text?.length > 0) {
        formatted += "\n\n";
      }

      // Format printed text section
      if (page.printed_text && page.printed_text.length > 0) {
        formatted += "PRINTED TEXT:\n";
        formatted += page.printed_text.join("\n");
      }
    });

    stringValue = formatted;
  }
  // Format page_biases field
  else if (isPageBiases && Array.isArray(fieldValue)) {
    const biasLines = [];

    fieldValue.forEach((page, index) => {
      biasLines.push(`--- PAGE ${index + 1} ---`);

      if (!page.biases || page.biases.length === 0) {
        biasLines.push("No biases identified for this page.");
      } else {
        page.biases.forEach((bias, biasIndex) => {
          biasLines.push(`Bias #${biasIndex + 1}:`);
          biasLines.push(`  Type: ${bias.type || 'Unknown'}`);
          biasLines.push(`  Level: ${bias.level || 'Unknown'}`);
          if (bias.explanation) {
            biasLines.push(`  Explanation: ${bias.explanation}`);
          }
          biasLines.push("");
        });
      }

      biasLines.push(""); // Add an extra line between pages
    });

    stringValue = biasLines.join("\n");
  }
  // Default handling for other fields
  else {
    stringValue = isList
      ? editableValue.join(' | ')
      : typeof editableValue === 'object'
        ? JSON.stringify(editableValue, null, 2)
        : String(editableValue || '');
  }

  const handleChange = ({ detail }) => {
    try {
      let newValue;

      // Parse transcription field
      if (isTranscription) {
        const text = detail.value;
        const pageMatches = text.split(/\n\n---\s*PAGE\s+\d+\s*---\s*\n\n/);

        // If there's no page separator, treat as a single page
        const pages = pageMatches.length > 0 ? pageMatches : [text];

        const parsedTranscription = pages.map(pageContent => {
          const result = { handwriting: [], printed_text: [] };

          // Split sections by headers
          const sections = {};
          let currentSection = null;

          pageContent.split("\n").forEach(line => {
            if (line.trim() === "HANDWRITING:") {
              currentSection = "handwriting";
            } else if (line.trim() === "PRINTED TEXT:") {
              currentSection = "printed_text";
            } else if (currentSection && line.trim()) {
              if (!sections[currentSection]) {
                sections[currentSection] = [];
              }
              sections[currentSection].push(line);
            }
          });

          // Populate result
          if (sections.handwriting) {
            result.handwriting = sections.handwriting;
          }
          if (sections.printed_text) {
            result.printed_text = sections.printed_text;
          }

          return result;
        });

        // Preserve the original structure with model_notes if it existed
        if (fieldValue && typeof fieldValue === 'object' && 'model_notes' in fieldValue) {
          newValue = {
            ...fieldValue,
            transcriptions: parsedTranscription
          };
        } else {
          newValue = parsedTranscription;
        }
      }
      // Page biases is read-only, but we'll include this for completeness
      else if (isPageBiases) {
        newValue = fieldValue;
      }
      // Handle list fields
      else if (isList) {
        newValue = detail.value
          .split('|')
          .map((item) => item.trim())
          .filter(Boolean);
      }
      // Try parsing JSON for object fields
      else if (detail.value.trim().startsWith('{') || detail.value.trim().startsWith('[')) {
        newValue = JSON.parse(detail.value);
      }
      // Default to string for all other cases
      else {
        newValue = detail.value;
      }

      // Update the metadata with the proper structure
      if (isTranscription && fieldValue && typeof fieldValue === 'object' && 'model_notes' in fieldValue) {
        // If we had a transcription with model_notes, preserve that structure
        if ('transcriptions' in fieldValue) {
          handleMetadataEdit(fieldKey, {
            ...fieldValue,
            transcriptions: Array.isArray(newValue) ? newValue : newValue.transcriptions
          });
        } else {
          const { model_notes } = fieldValue;
          handleMetadataEdit(fieldKey, {
            model_notes,
            ...Array.isArray(newValue) ? { transcriptions: newValue } : newValue
          });
        }
      }
      // Handle standard explanation/value pattern
      else if (fieldValue && typeof fieldValue === 'object' && 'explanation' in fieldValue && 'value' in fieldValue) {
        handleMetadataEdit(fieldKey, {
          ...fieldValue,
          value: newValue
        });
      }
      // Default case
      else {
        handleMetadataEdit(fieldKey, newValue);
      }
    } catch (e) {
      console.error(`Error updating ${fieldKey}:`, e);
      // On error, just store the raw text
      if (fieldValue && typeof fieldValue === 'object') {
        if ('transcriptions' in fieldValue) {
          handleMetadataEdit(fieldKey, {
            ...fieldValue,
            transcriptions: detail.value
          });
        } else if ('value' in fieldValue) {
          handleMetadataEdit(fieldKey, {
            ...fieldValue,
            value: detail.value
          });
        } else {
          handleMetadataEdit(fieldKey, detail.value);
        }
      } else {
        handleMetadataEdit(fieldKey, detail.value);
      }
    }
  };

  return (
    <Container header={<Header variant="h3">{formattedKey}</Header>}>
      <SpaceBetween size="m">
        {rationale && (
          <Box padding="s">
            <SpaceBetween size="xs">
              <Header variant="h4">Rationale</Header>
              <div>{rationale}</div>
            </SpaceBetween>
          </Box>
        )}
        <Textarea
          value={stringValue}
          onChange={handleChange}
          rows={isTranscription || isPageBiases ? 12 : 5}
          placeholder={
            isTranscription
              ? "HANDWRITING:\n(enter handwritten text here)\n\nPRINTED TEXT:\n(enter printed text here)"
              : isPageBiases
                ? "Bias information is read-only"
                : isList
                  ? "e.g. value1 | value2 | value3"
                  : `Enter ${formattedKey.toLowerCase()} here...`
          }
          readOnly={isPageBiases}
        />
      </SpaceBetween>
    </Container>
  );
}

export default MetadataSection;
