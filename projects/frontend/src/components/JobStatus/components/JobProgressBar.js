/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import { ProgressBar } from "@cloudscape-design/components";

const JobProgressBar = ({ progressPercentage, statusCounts, totalWorks }) => {
  return (
    <ProgressBar
      value={progressPercentage}
      label={`${progressPercentage}% complete`}
      description={`${statusCounts.completed} of ${totalWorks} items processed`}
      status={statusCounts.failed > 0 ? "error" : "in-progress"}
    />
  );
};

export default JobProgressBar;
