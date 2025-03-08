/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Container,
  SpaceBetween,
  Header,
  Box,
  Spinner
} from "@cloudscape-design/components";
import { useMetadataContext } from '../MetadataContext';
import MetadataSection from './MetadataSection';

function MetadataEditor() {
  const { metadata, selectedWork, isLoading } = useMetadataContext();

  // First check if we're loading
  if (isLoading && selectedWork) {
    return (
      <Container>
        <Box textAlign="center" padding="l">
          <SpaceBetween size="s" direction="vertical" alignItems="center">
            <Spinner />
            <Box variant="p">Loading metadata details...</Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  // Explicitly check if selectedWork is null or undefined
  if (!selectedWork) {
    return (
      <Container>
        <Box textAlign="center" padding="xl">
          <Box variant="h3">Select a document</Box>
          <Box variant="p">
            Please select a document from the list to view and edit its metadata.
          </Box>
        </Box>
      </Container>
    );
  }

  // Check if metadata is loading or not available
  if (!metadata) {
    return (
      <Container>
        <Box textAlign="center" padding="l">
          <SpaceBetween size="s" direction="vertical" alignItems="center">
            <Spinner />
            <Box variant="p">Loading metadata...</Box>
          </SpaceBetween>
        </Box>
      </Container>
    );
  }

  // If we have both selectedWork and metadata, render the metadata editor
  const priority_fields = [
    'page_biases',
    'description',
    'transcription',
    'contextual_info',
    'publication_info',
    'location',
    'format',
    'genre',
    'topics',
    'date',
    'people',
    'actions',
    'objects',
  ];
  return (
    <Container
      header={
        <Header variant="h2">
          Document Metadata
        </Header>
      }
    >
      <SpaceBetween size="l">
        {/* Render prioritized fields first in the specified order */}
        {priority_fields.map(key =>
          metadata[key] !== undefined && (
            <MetadataSection key={key} fieldKey={key} fieldValue={metadata[key]} />
          )
        )}

        {/* Then render all remaining fields */}
        {Object.entries(metadata)
          .filter(([key]) => !priority_fields.includes(key))
          .map(([key, value]) => (
            <MetadataSection key={key} fieldKey={key} fieldValue={value} />
          ))
        }
      </SpaceBetween>
    </Container>
  );
}

export default MetadataEditor;
