import React from 'react';
import {
  Container,
  Header,
  FormField,
  Textarea,
  SpaceBetween
} from "@cloudscape-design/components";
import { useMetadataContext } from '../MetadataContext';
import { formatValue } from '../utils/formatter';

function MetadataSection({ fieldKey, fieldValue }) {
  const { handleMetadataEdit } = useMetadataContext();

  // Skip certain fields from being displayed
  if (fieldKey === 'image_s3_uris' || fieldKey === 'work_id' ||
      fieldKey === 'job_name' || fieldKey === 'work_status') {
    return null;
  }

  // Format the field key for display
  const formattedKey = fieldKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

  // Handle empty array field
  if (Array.isArray(fieldValue) && fieldValue.length === 0) {
    return (
      <Container
        header={<Header variant="h3">{formattedKey}</Header>}
      >
        <FormField
          label="Value"
          description="Enter comma-separated values for this field. Currently empty."
        >
          <Textarea
            value=""
            onChange={({ detail }) => handleMetadataEdit(fieldKey,
              detail.value.split(',').filter(item => item.trim().length > 0)
            )}
            rows={2}
            placeholder="Enter comma-separated values..."
          />
        </FormField>
      </Container>
    );
  }

  // Handle nested structure with explanation and value
  const isNestedStructure = fieldValue &&
    typeof fieldValue === 'object' &&
    ('explanation' in fieldValue || 'value' in fieldValue);

  if (isNestedStructure) {
    return (
      <Container
        header={<Header variant="h3">{formattedKey}</Header>}
      >
        <SpaceBetween size="m">
          <FormField label="Explanation">
            <Textarea
              value={fieldValue.explanation || ''}
              onChange={({ detail }) => handleMetadataEdit(fieldKey, {
                ...fieldValue,
                explanation: detail.value
              })}
              rows={3}
            />
          </FormField>

          <FormField
            label="Value"
            description={Array.isArray(fieldValue.value) ?
              "Enter values separated by commas" :
              "Enter value for this field"}
          >
            <Textarea
              value={fieldValue.value ? formatValue(fieldValue.value) : ''}
              onChange={({ detail }) => handleMetadataEdit(fieldKey, {
                ...fieldValue,
                value: detail.value
              })}
              rows={3}
              placeholder={Array.isArray(fieldValue.value) ?
                "e.g. value1, value2, value3" :
                "Enter value here..."}
            />
          </FormField>
        </SpaceBetween>
      </Container>
    );
  }

  // Handle array fields
  if (Array.isArray(fieldValue)) {
    return (
      <Container
        header={<Header variant="h3">{formattedKey}</Header>}
      >
        <FormField
          label="Value"
          description="Enter values separated by commas"
        >
          <Textarea
            value={formatValue(fieldValue)}
            onChange={({ detail }) => handleMetadataEdit(fieldKey,
              detail.value.split(',').map(item => item.trim()).filter(item => item)
            )}
            rows={4}
            placeholder="e.g. value1, value2, value3"
          />
        </FormField>
      </Container>
    );
  }

  // Default case: simple value field
  return (
    <Container
      header={<Header variant="h3">{formattedKey}</Header>}
    >
      <FormField
        label="Value"
        description={
          typeof fieldValue === 'object' ?
            "JSON object - Edit carefully" :
            `Enter ${typeof fieldValue} value`
        }
      >
        <Textarea
          value={formatValue(fieldValue)}
          onChange={({ detail }) => handleMetadataEdit(fieldKey, detail.value)}
          rows={4}
          placeholder={`Enter ${formattedKey.toLowerCase()} here...`}
        />
      </FormField>
    </Container>
  );
}

export default MetadataSection;