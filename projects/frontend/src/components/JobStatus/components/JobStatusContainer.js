/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

// components/JobStatus/components/JobStatusContainer.js

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  Box,
  Spinner,
} from "@cloudscape-design/components";
import JobProgressBar from './JobProgressBar';

const JobStatusContainer = ({ job, navigate, onRefresh, isRefreshing }) => {
  const getStatusCounts = (job) => {
    const inQueue = job.works.filter(w => w.work_status === 'IN QUEUE').length;
    const inProgress = job.works.filter(w => w.work_status === 'IN PROGRESS').length;
    const readyForReview = job.works.filter(w => w.work_status === 'READY FOR REVIEW').length;
    const failed = job.works.filter(w => w.work_status === 'FAILED TO PROCESS').length;
    const reviewed = job.works.filter(w => w.work_status === 'REVIEWED').length;
    return { inQueue, inProgress, readyForReview, failed, reviewed };
  };

  const handleViewResults = (job, work) => {
    console.log('Navigating with data:', {
      jobName: job.job_name,
      workId: work.work_id,
      jobType: job.job_type
    });

    if (job.job_type === 'metadata') {
      navigate(`/results/metadata/${job.job_name}`, {
        state: {
          jobName: job.job_name,
          workId: work.work_id
        }
      });
    } else if (job.job_type === 'bias') {
      navigate(`/results/bias/${job.job_name}`, {
        state: {
          jobName: job.job_name,
          workId: work.work_id
        }
      });
    } else {
      console.error('Unknown job type:', job.job_type);
    }
  };

  const statusCounts = getStatusCounts(job);
  const totalWorks = job.works.length;

  return (
    <Container
      header={
        <Header
          variant="h2"
          actions={
            <SpaceBetween direction="horizontal" size="xs">
              <div className="refresh-container">
                <Button
                  onClick={() => onRefresh(job.job_name)}
                  loading={isRefreshing}
                >
                  Refresh
                </Button>
                {isRefreshing && <Spinner size="normal" />}
              </div>
              <Button
                variant="primary"
                onClick={() => handleViewResults(job, job.works[0])}
              >
                View Results
              </Button>
            </SpaceBetween>
          }
          description={`Job Type: ${job.job_type.toUpperCase()}`}
        >
          {job.job_name}
        </Header>
      }
    >
      <SpaceBetween size="l">
        <Box>
          <Box variant="awsui-key-label">Progress</Box>
          <JobProgressBar
            statusCounts={statusCounts}
            totalWorks={totalWorks}
          />
        </Box>
      </SpaceBetween>
    </Container>
  );
};

export default JobStatusContainer;
