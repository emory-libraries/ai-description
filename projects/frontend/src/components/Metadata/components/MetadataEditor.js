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

  if (!selectedWork || !metadata) {
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

  return (
    <Container
      header={
        <Header variant="h2">
          Document Metadata
        </Header>
      }
    >
      <SpaceBetween size="l">
        {Object.entries(metadata).map(([key, value]) => (
          <MetadataSection key={key} fieldKey={key} fieldValue={value} />
        ))}
      </SpaceBetween>
    </Container>
  );
}

export default MetadataEditor;