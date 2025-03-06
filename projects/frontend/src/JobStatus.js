/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext'; // Use your custom auth context
import {
  AppLayout,
  Container,
  ContentLayout,
  SpaceBetween,
  Header,
  Box,
  Button,
  Form,
  FormField,
  Input,
  Alert,
  Spinner,
  Cards,
  ProgressBar,
  ColumnLayout,
  ExpandableSection,
  Badge,
  BreadcrumbGroup
} from "@cloudscape-design/components";
import { AWSSideNavigation } from './components/Navigation';

const JobStatus = () => {
  const { token, logout } = useAuth(); // Use your custom auth hook
  const navigate = useNavigate();
  const [jobs, setJobs] = useState(() => {
    const savedJobs = localStorage.getItem('jobStatus');
    return savedJobs ? new Map(JSON.parse(savedJobs)) : new Map();
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [jobName, setJobName] = useState('');
  const [submittedJobName, setSubmittedJobName] = useState(() => {
    return localStorage.getItem('submittedJobName') || '';
  });

  useEffect(() => {
    localStorage.setItem('jobStatus', JSON.stringify(Array.from(jobs.entries())));
  }, [jobs]);

  useEffect(() => {
    localStorage.setItem('submittedJobName', submittedJobName);
  }, [submittedJobName]);

  const handleSubmitJobName = (e) => {
    e.preventDefault();
    const trimmedJobName = jobName.trim();
    if (trimmedJobName) {
      if (trimmedJobName !== submittedJobName) {
        setJobs(new Map());
        setError(null);
      }
      setSubmittedJobName(trimmedJobName);
    }
  };

  const checkJobProgress = async () => {
    if (!token || !submittedJobName) return;

    try {
      setIsLoading(true);
      console.log(`Fetching from: /api/job_progress?job_name=${submittedJobName}`);

      const response = await fetch(
        `/api/job_progress?job_name=${submittedJobName}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        
        // Handle unauthorized responses (token expired)
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          return;
        }
        
        setJobs(new Map());
        return;
      }

      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('JSON Parse Error:', parseError);
        return;
      }

      const newJobs = new Map();
      const jobKey = submittedJobName;
      const workItems = [];
      if (data.job_progress) {
        Object.entries(data.job_progress).forEach(([status, ids]) => {
          ids.forEach(id => {
            workItems.push({
              work_id: id,
              status: status,
              job_name: jobKey,
              job_type: data.job_type
            });
          });
        });
      }

      const jobData = {
        job_name: jobKey,
        job_type: data.job_type || 'unknown',
        works: workItems
      };

      newJobs.set(jobKey, jobData);
      setJobs(newJobs);

    } catch (err) {
      console.error('Error checking job progress:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (token && submittedJobName) {
      checkJobProgress();
      const intervalId = setInterval(checkJobProgress, 5000);
      return () => clearInterval(intervalId);
    }
  }, [token, submittedJobName]);

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

  const getStatusCounts = (job) => {
    const inQueue = job.works.filter(w => w.status === 'IN_QUEUE').length;
    const inProgress = job.works.filter(w => w.status === 'IN_PROGRESS' || w.status === 'PROCESSING').length;
    const completed = job.works.filter(w => w.status === 'READY FOR REVIEW').length;
    const failed = job.works.filter(w => w.status === 'FAILED TO PROCESS').length;
    return { inQueue, inProgress, completed, failed };
  };

  const breadcrumbItems = [
    { text: 'Document Analysis Service', href: '/' },
    { text: 'Job Status', href: '/' }
  ];

  // Since this is already in a PrivateRoute, we don't need the isAuthenticated check
  // The PrivateRoute component will handle redirecting to login if not authenticated

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/" />}
      toolsHide={true}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      content={
        <ContentLayout header={<Header variant="h1">Document Analysis Job Status</Header>}>
          <SpaceBetween size="l">
            <Container
              header={
                <Header variant="h2" description="Enter a job name to retrieve status information">
                  Job Lookup
                </Header>
              }
            >
              <Form
                actions={
                  <Button
                    variant="primary"
                    formAction="submit"
                    onClick={handleSubmitJobName}
                    disabled={!jobName.trim()}
                  >
                    Submit
                  </Button>
                }
              >
                <FormField
                  label="Job name"
                  description="Enter the job identifier to view processing status"
                >
                  <Input
                    value={jobName}
                    onChange={({ detail }) => setJobName(detail.value)}
                    placeholder="Enter job name"
                  />
                </FormField>
              </Form>
            </Container>

            {error && (
              <Alert type="error" header="Error">
                {error}
              </Alert>
            )}

            {isLoading && submittedJobName && jobs.size === 0 && (
              <Container>
                <Box textAlign="center" padding="l">
                  <SpaceBetween size="s" direction="vertical" alignItems="center">
                    <Spinner size="large" />
                    <Box variant="p">Retrieving job information...</Box>
                  </SpaceBetween>
                </Box>
              </Container>
            )}

            {submittedJobName && jobs.size > 0 && Array.from(jobs.values()).map(job => {
              const statusCounts = getStatusCounts(job);
              const totalWorks = job.works.length;
              const progressPercentage = Math.round((statusCounts.completed / totalWorks) * 100);

              return (
                <Container
                  key={job.job_name}
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

                    <Box>
                      <Box variant="awsui-key-label">Overall Progress</Box>
                      <ProgressBar
                        value={progressPercentage}
                        label={`${progressPercentage}% complete`}
                        description={`${statusCounts.completed} of ${totalWorks} items processed`}
                        status={statusCounts.failed > 0 ? "error" : "in-progress"}
                      />
                    </Box>

                    <ExpandableSection headerText="Work Items Details">
                      <Cards
                        cardDefinition={{
                          header: item => item.work_id,
                          sections: [
                            {
                              id: "status",
                              header: "Status",
                              content: item => {
                                let statusType = "info";
                                if (item.status === "READY FOR REVIEW") statusType = "success";
                                if (item.status === "FAILED TO PROCESS") statusType = "error";

                                return <Badge color={statusType}>{item.status}</Badge>;
                              }
                            }
                          ]
                        }}
                        cardsPerRow={[
                          { cards: 1 },
                          { minWidth: 500, cards: 2 }
                        ]}
                        items={job.works}
                        loadingText="Loading work items"
                        empty={
                          <Box textAlign="center" color="text-body-secondary">
                            <b>No work items found</b>
                            <Box padding={{ bottom: "s" }}>
                              This job has no associated work items
                            </Box>
                          </Box>
                        }
                      />
                    </ExpandableSection>
                  </SpaceBetween>
                </Container>
              );
            })}

            {submittedJobName && jobs.size === 0 && !isLoading && (
              <Container>
                <Box textAlign="center" padding="l">
                  <Box variant="h3">No data found</Box>
                  <Box variant="p">No job information found for "{submittedJobName}"</Box>
                </Box>
              </Container>
            )}
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
};

export default JobStatus;
