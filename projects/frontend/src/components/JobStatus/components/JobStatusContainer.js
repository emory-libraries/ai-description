/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  ExpandableSection,
  Box
} from "@cloudscape-design/components";
import JobProgressBar from './JobProgressBar';
import WorkItemsCards from './WorkItemCards';

const JobStatusContainer = ({ job, navigate }) => {
  const getStatusCounts = (job) => {
    const inQueue = job.works.filter(w => w.work_status === 'IN QUEUE').length;
    const inProgress = job.works.filter(w => w.work_status === 'IN PROGRESS').length;
    const completed = job.works.filter(w => w.work_status === 'READY FOR REVIEW').length;
    const failed = job.works.filter(w => w.work_status === 'FAILED TO PROCESS').length;
    const reviewed = job.works.filter(w => w.work_status === 'REVIEWED').length;
    return { inQueue, inProgress, completed, failed, reviewed };
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
            statusCounts.completed > 0 && (
              <Button
                variant="primary"
                onClick={() => handleViewResults(job, job.works[0])}
              >
                View Results
              </Button>
            )
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

        <ExpandableSection headerText="Work Items Details">
          <WorkItemsCards works={job.works} />
        </ExpandableSection>
      </SpaceBetween>
    </Container>
  );
};

export default JobStatusContainer;
