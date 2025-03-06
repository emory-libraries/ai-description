/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Box,
  Spinner,
  SpaceBetween
} from "@cloudscape-design/components";

/**
 * Component for displaying images with loading state
 */
export const ImageViewer = ({ imageUrl }) => {
  return imageUrl ? (
    <img
      src={imageUrl}
      alt="Content with detected bias"
      style={{
        maxWidth: '100%',
        maxHeight: '500px',
        objectFit: 'contain'
      }}
    />
  ) : (
    <Box textAlign="center" padding="l">
      <SpaceBetween size="s" direction="vertical" alignItems="center">
        <Spinner />
        <Box variant="p">Loading image...</Box>
      </SpaceBetween>
    </Box>
  );
};