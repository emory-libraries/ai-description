/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

// components/JobStatus/index.js

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';
import {
  AppLayout,
  ContentLayout,
  SpaceBetween,
  Header,
} from "@cloudscape-design/components";
import { AWSSideNavigation } from '../Navigation';
import JobLookupForm from './components/JobLookupForm';
import LoadingState from './components/LoadingState';
import ErrorAlert from './components/ErrorAlert';
import JobStatusContainer from './components/JobStatusContainer';
import useJobStatus from './hooks/useJobStatus';
import NoDataFound from './components/NoDataFound';
const JobStatus = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [jobName, setJobName] = useState('');
  const {
    jobs,
    submittedJobName,
    setSubmittedJobName,
    isLoading,
    error,
    isRefreshing,
    checkJobProgress,
  } = useJobStatus(token, navigate);

  const handleRefresh = (jobName) => {
    setSubmittedJobName(jobName);
    checkJobProgress(jobName, true);
  };

  const handleSubmitJobName = (e) => {
    e.preventDefault();
    const trimmedJobName = jobName.trim();
    if (trimmedJobName) {
      setSubmittedJobName(trimmedJobName);
      checkJobProgress(trimmedJobName);
    }
  };

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/" />}
      toolsHide={true}
      navigationHide={true}
      content={
        <ContentLayout header={<Header variant="h1">Document Analysis Service</Header>}>
          <SpaceBetween size="l">
            <JobLookupForm
              jobName={jobName}
              setJobName={setJobName}
              handleSubmitJobName={handleSubmitJobName}
            />

            {error && <ErrorAlert message={error} />}

            {isLoading && submittedJobName && jobs.size === 0 && (
              <LoadingState />
            )}

            {submittedJobName && jobs.size > 0 && Array.from(jobs.values()).map(job => (
              <JobStatusContainer
                key={job.job_name}
                job={job}
                navigate={navigate}
                onRefresh={handleRefresh}
                isRefreshing={isRefreshing}
                />
            ))}

            {submittedJobName && jobs.size === 0 && !isLoading && (
              <NoDataFound jobName={submittedJobName} />
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
};

export default JobStatus;
