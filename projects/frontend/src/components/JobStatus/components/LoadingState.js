/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

import React from 'react';
import { Container, Box, SpaceBetween, Spinner } from '@cloudscape-design/components';

const LoadingState = () => {
  return (
    <Container>
      <Box textAlign="center" padding="l">
        <SpaceBetween size="s" direction="vertical" alignItems="center">
          <Spinner size="large" />
          <Box variant="p">Retrieving job information...</Box>
        </SpaceBetween>
      </Box>
    </Container>
  );
};

export default LoadingState;
