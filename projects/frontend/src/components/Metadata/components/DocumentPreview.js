import React from 'react';
import {
  Container,
  Header,
  Box,
  Spinner,
  Button,
  SpaceBetween,
  Grid,
  StatusIndicator
} from "@cloudscape-design/components";
import { useMetadataContext } from '../MetadataContext';

function DocumentPreview() {
  const {
    metadata,
    imageData,
    modifiedFields,
    updateMetadata,
    selectedWork,
    updateReviewStatus
  } = useMetadataContext();

  if (!metadata) {
    return null;
  }

  const totalImages = metadata.image_s3_uris?.length || 0;
  const additionalImages = totalImages - 2;
  const isReviewed = selectedWork?.work_status === "REVIEWED";

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              {isReviewed ? (
                <Button onClick={() => updateReviewStatus(selectedWork, "READY FOR REVIEW")}>
                  Rescind reviewed status
                </Button>
              ) : (
                <Button onClick={() => updateReviewStatus(selectedWork, "REVIEWED")}>
                  Mark as reviewed
                </Button>
              )}
              <Button
                variant="primary"
                disabled={Object.keys(modifiedFields).length === 0}
                onClick={updateMetadata}
              >
                Save Changes
              </Button>
            </SpaceBetween>
          }
        >
          Document Preview
        </Header>
      }
    >
      {/* Rest of component remains the same */}
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
            key={`image-${index}-${uri}`}
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
      {additionalImages > 0 && (
        <Box textAlign="center" padding="m">
          <StatusIndicator type="info">
            {additionalImages} additional {additionalImages === 1 ? 'image' : 'images'} not shown
          </StatusIndicator>
        </Box>
      )}
    </Container>
  );
}

export default DocumentPreview;