/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import {
  ColumnLayout,
  Box
} from "@cloudscape-design/components";

const JobStatusMetrics = ({ statusCounts }) => {
  return (
    <ColumnLayout columns={4} variant="text-grid">
      <div>
        <Box variant="awsui-key-label">In Queue</Box>
        <Box variant="awsui-value-large">{statusCounts.inQueue}</Box>
      </div>
      <div>
        <Box variant="awsui-key-label">In Progress</Box>
        <Box variant="awsui-value-large">{statusCounts.inProgress}</Box>
      </div>
      <div>
        <Box variant="awsui-key-label">Completed</Box>
        <Box variant="awsui-value-large">{statusCounts.completed}</Box>
      </div>
      <div>
        <Box variant="awsui-key-label">Failed</Box>
        <Box
          variant="awsui-value-large"
          color={statusCounts.failed > 0 ? "text-status-error" : undefined}
        >
          {statusCounts.failed}
        </Box>
      </div>
    </ColumnLayout>
  );
};

export default JobStatusMetrics;
