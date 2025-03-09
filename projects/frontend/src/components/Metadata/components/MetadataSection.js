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

  // Determine if we have a special field structure with a rationale
  let rationale = null;
  let editableValue = fieldValue;
  let updatePath = null;
  let isList = false;

  // Case 1: Object with explanation and value
  if (fieldValue && typeof fieldValue === 'object') {
    if ('explanation' in fieldValue && 'value' in fieldValue) {
      rationale = fieldValue.explanation;
      editableValue = fieldValue.value;
      updatePath = 'value';
      isList = Array.isArray(fieldValue.value);
    }
    // Case 2: Transcription with model_notes
    else if (fieldKey === 'transcription' && 'transcriptions' in fieldValue && 'model_notes' in fieldValue) {
      rationale = fieldValue.model_notes;
      editableValue = fieldValue.transcriptions;
      updatePath = 'transcriptions';
    }
  } else if (Array.isArray(fieldValue)) {
    isList = true;
  }

  // Convert the editable value to a string for display
  const stringValue = isList
    ? editableValue.join(' | ')
    : typeof editableValue === 'object'
      ? JSON.stringify(editableValue, null, 2)
      : String(editableValue || '');

  const handleChange = ({ detail }) => {
    try {
      let newValue;

      // Handle different value types
      if (isList) {
        newValue = detail.value
          .split('|')
          .map((item) => item.trim())
          .filter(Boolean);
      } else if (detail.value.trim().startsWith('{') || detail.value.trim().startsWith('[')) {
        newValue = JSON.parse(detail.value);
      } else {
        newValue = detail.value;
      }

      // Update accordingly based on field structure
      if (updatePath) {
        handleMetadataEdit(fieldKey, {
          ...fieldValue,
          [updatePath]: newValue,
        });
      } else {
        handleMetadataEdit(fieldKey, newValue);
      }
    } catch (e) {
      // Fallback to string if JSON parsing fails
      if (updatePath) {
        handleMetadataEdit(fieldKey, {
          ...fieldValue,
          [updatePath]: detail.value,
        });
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
          rows={5}
          placeholder={isList ? 'e.g. value1 | value2 | value3' : `Enter ${formattedKey.toLowerCase()} here...`}
        />
      </SpaceBetween>
    </Container>
  );
}

export default MetadataSection;
