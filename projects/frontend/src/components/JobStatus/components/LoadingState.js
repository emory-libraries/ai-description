import React from 'react';
import {
  Container,
  Box,
  SpaceBetween,
  Spinner
} from "@cloudscape-design/components";

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