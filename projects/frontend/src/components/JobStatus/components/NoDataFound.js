/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import {
  Container,
  Box
} from "@cloudscape-design/components";

const NoDataFound = ({ jobName }) => {
  return (
    <Container>
      <Box textAlign="center" padding="l">
        <Box variant="h3">No data found</Box>
        <Box variant="p">No job information found for "{jobName}"</Box>
      </Box>
    </Container>
  );
};

export default NoDataFound;
