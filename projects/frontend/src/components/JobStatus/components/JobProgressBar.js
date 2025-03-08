/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import { Box } from "@cloudscape-design/components";

const JobProgressBar = ({ statusCounts, totalWorks }) => {
  // Calculate percentages for each status
  const inQueuePercent = (statusCounts.inQueue / totalWorks) * 100;
  const inProgressPercent = (statusCounts.inProgress / totalWorks) * 100;
  const readyPercent = (statusCounts.readyForReview / totalWorks) * 100;
  const reviewedPercent = (statusCounts.reviewed / totalWorks) * 100;
  const failedPercent = (statusCounts.failed / totalWorks) * 100;

  // Define status colors
  const statusColors = {
    inQueue: "#CCCCCC", // grey
    inProgress: "#F2C166", // yellow
    readyForReview: "#5095E0", // blue
    reviewed: "#60BD68", // green
    failed: "#E05050"  // red
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          height: '16px',
          width: '100%',
          borderRadius: '8px',
          overflow: 'hidden',
          backgroundColor: '#F1F1F1', // background for empty bar
        }}
      >
        {/* In Queue */}
        {inQueuePercent > 0 && (
          <div
            style={{
              width: `${inQueuePercent}%`,
              backgroundColor: statusColors.inQueue,
              height: '100%',
            }}
            title={`In Queue: ${statusCounts.inQueue} items (${Math.round(inQueuePercent)}%)`}
          />
        )}

        {/* In Progress */}
        {inProgressPercent > 0 && (
          <div
            style={{
              width: `${inProgressPercent}%`,
              backgroundColor: statusColors.inProgress,
              height: '100%',
            }}
            title={`In Progress: ${statusCounts.inProgress} items (${Math.round(inProgressPercent)}%)`}
          />
        )}

        {/* Ready For Review */}
        {readyPercent > 0 && (
          <div
            style={{
              width: `${readyPercent}%`,
              backgroundColor: statusColors.readyForReview,
              height: '100%',
            }}
            title={`Ready for Review: ${statusCounts.readyForReview} items (${Math.round(readyPercent)}%)`}
          />
        )}

        {/* Reviewed */}
        {reviewedPercent > 0 && (
          <div
            style={{
              width: `${reviewedPercent}%`,
              backgroundColor: statusColors.reviewed,
              height: '100%',
            }}
            title={`Reviewed: ${statusCounts.reviewed} items (${Math.round(reviewedPercent)}%)`}
          />
        )}

        {/* Failed */}
        {failedPercent > 0 && (
          <div
            style={{
              width: `${failedPercent}%`,
              backgroundColor: statusColors.failed,
              height: '100%',
            }}
            title={`Failed: ${statusCounts.failed} items (${Math.round(failedPercent)}%)`}
          />
        )}
      </div>

      {/* Legend */}
      <Box padding={{ top: 's' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
          {statusCounts.inQueue > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: statusColors.inQueue, borderRadius: '2px' }}></div>
              <span>In Queue ({statusCounts.inQueue})</span>
            </div>
          )}
          {statusCounts.inProgress > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: statusColors.inProgress, borderRadius: '2px' }}></div>
              <span>In Progress ({statusCounts.inProgress})</span>
            </div>
          )}
          {statusCounts.readyForReview > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: statusColors.readyForReview, borderRadius: '2px' }}></div>
              <span>Ready for Review ({statusCounts.readyForReview})</span>
            </div>
          )}
          {statusCounts.reviewed > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: statusColors.reviewed, borderRadius: '2px' }}></div>
              <span>Reviewed ({statusCounts.reviewed})</span>
            </div>
          )}
          {statusCounts.failed > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', backgroundColor: statusColors.failed, borderRadius: '2px' }}></div>
              <span>Failed ({statusCounts.failed})</span>
            </div>
          )}
        </div>
      </Box>
    </div>
  );
};

export default JobProgressBar;
