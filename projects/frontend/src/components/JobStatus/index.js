/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';
import {
  AppLayout,
  ContentLayout,
  SpaceBetween,
  Header,
  BreadcrumbGroup
} from "@cloudscape-design/components";
import { AWSSideNavigation } from '../Navigation';
import JobLookupForm from './components/JobLookupForm';
import LoadingState from './components/LoadingState';
import ErrorAlert from './components/ErrorAlert';
import JobStatusContainer from './components/JobStatusContainer';
import useJobStatus from './hooks/useJobStatus';
import NoDataFound from './components/NoDataFound';
import { buildFrontendPath } from '../../utils/frontendPaths';
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
    checkJobProgress
  } = useJobStatus(token, navigate);

  const handleSubmitJobName = (e) => {
    e.preventDefault();
    const trimmedJobName = jobName.trim();
    if (trimmedJobName) {
      setSubmittedJobName(trimmedJobName);
      checkJobProgress(trimmedJobName);
    }
  };

  const breadcrumbItems = [
    { text: 'Document Analysis Service', href: buildFrontendPath('/') },
    { text: 'Job Status', href: buildFrontendPath('/') }
  ];

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/" />}
      toolsHide={true}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      defaultHideNavigation={true}
      content={
        <ContentLayout header={<Header variant="h1">Document Analysis Job Status</Header>}>
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
