/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Container,
  Grid,
  Header,
  Box,
  SpaceBetween,
  ColumnLayout,
  StatusIndicator
} from "@cloudscape-design/components";
import { getBiasLevelColor } from '../utils/biasHelpers';
import { ImageViewer } from './ImageViewer';

/**
 * Component displaying detailed information about a selected bias
 */
export const BiasDetails = ({ bias, imageUrl }) => {
  return (
    <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
      {/* Left side - Image */}
      <Container>
        <ImageViewer imageUrl={imageUrl} />
      </Container>

      {/* Right side - Bias details */}
      <Container header={<Header variant="h3">Bias Details</Header>}>
        <SpaceBetween size="l">
          <ColumnLayout columns={2} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">Type</Box>
              <Box variant="awsui-value-large">{bias.type}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">Level</Box>
              <Box>
                <StatusIndicator type={getBiasLevelColor(bias.level)}>
                  {bias.level} Risk
                </StatusIndicator>
              </Box>
            </div>
          </ColumnLayout>
          <div>
            <Box variant="awsui-key-label">Explanation</Box>
            <Box variant="p">{bias.explanation}</Box>
          </div>
        </SpaceBetween>
      </Container>
    </Grid>
  );
};
