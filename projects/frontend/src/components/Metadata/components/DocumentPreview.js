/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Container,
  Header,
  Box,
  Spinner,
  Button,
  SpaceBetween,
  Grid
} from "@cloudscape-design/components";
import { useMetadataContext } from '../MetadataContext';

function DocumentPreview() {
  const { 
    metadata,
    imageData,
    modifiedFields,
    updateMetadata
  } = useMetadataContext();

  if (!metadata) {
    return null;
  }

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            <Button
              variant="primary"
              disabled={Object.keys(modifiedFields).length === 0}
              onClick={updateMetadata}
            >
              Save Changes
            </Button>
          }
        >
          Document Preview
        </Header>
      }
    >
      <Grid
        gridDefinition={
          metadata.image_s3_uris.length === 1
            ? [{ colspan: 12 }]
            : [
                { colspan: { default: 12, xxs: 6 } },
                { colspan: { default: 12, xxs: 6 } }
              ]
        }
      >
        {metadata?.image_s3_uris?.slice(0, 2).map((uri, index) => (
          <div
            key={uri}
            style={{
              padding: '1rem',
              textAlign: 'center',
              margin: metadata.image_s3_uris.length === 1 ? '0 auto' : '0'  // Center if single image
            }}
          >
            {imageData[uri] ? (
              <img
                src={imageData[uri]}
                alt={`Page ${index + 1}`}
                style={{
                  maxWidth: '100%',
                  maxHeight: '400px',
                  objectFit: 'contain',
                  border: '1px solid #eaeded',
                  borderRadius: '4px',
                  padding: '8px',
                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                }}
              />
            ) : (
              <Box
                padding="xl"
                textAlign="center"
                color="text-status-inactive"
                fontSize="heading-m"
                className="custom-document-placeholder"
              >
                <SpaceBetween size="s" direction="vertical" alignItems="center">
                  <Spinner />
                  <Box variant="p">Loading image {index + 1}...</Box>
                </SpaceBetween>
              </Box>
            )}
          </div>
        ))}
      </Grid>
    </Container>
  );
}

export default DocumentPreview;
