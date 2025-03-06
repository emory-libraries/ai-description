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