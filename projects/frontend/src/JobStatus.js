import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from "react-oidc-context";
import { 
  View,
  Card, 
  Button, 
  Heading, 
  Flex, 
  Text,
  Alert,
  Loader,
  Collection,
  Divider,
  TextField
} from '@aws-amplify/ui-react';

const API_ENDPOINT = 'https://pn17lumhd3.execute-api.us-east-1.amazonaws.com/dev';

const JobStatus = () => {
  const auth = useAuth();
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
      // Only clear jobs if submitting a different job name
      if (trimmedJobName !== submittedJobName) {
        setJobs(new Map());
        setError(null);
      }
      setSubmittedJobName(trimmedJobName);
    }
  };

  const checkJobProgress = async () => {
    if (!auth.user?.access_token || !submittedJobName) return;
  
    try {
      setIsLoading(true);
      const response = await fetch(
        `${API_ENDPOINT}/job_progress?job_name=${submittedJobName}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
  
      if (!response.ok) {
        setJobs(new Map());
        setError(null);
        return;
      }
  
      const data = await response.json();
      console.log('API Response:', data); // Debug log to see the response
  
      const newJobs = new Map();
      const jobKey = submittedJobName;
  
      // Handle the job_progress structure from the Lambda
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
        job_type: data.job_type,
        works: workItems
      };
  
      newJobs.set(jobKey, jobData);
      setJobs(newJobs);
  
    } catch (err) {
      console.error('Error checking job progress:', err);
      setError(`Failed to check job progress: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  
  
  useEffect(() => {
    if (auth.isAuthenticated && auth.user?.access_token && submittedJobName) {
      checkJobProgress();
      const intervalId = setInterval(checkJobProgress, 5000);
      return () => clearInterval(intervalId);
    }
  }, [auth.isAuthenticated, auth.user?.access_token, submittedJobName]);

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

  if (!auth.isAuthenticated) {
    return (
      <View padding="medium">
        <Card variation="elevated">
          <Flex direction="column" gap="medium" alignItems="center">
            <Heading level={3}>Please sign in to continue</Heading>
            <Button
              variation="primary"
              onClick={() => auth.signinRedirect()}
              loadingText="Redirecting..."
            >
              Sign In
            </Button>
          </Flex>
        </Card>
      </View>
    );
  }

  return (
    <View padding="medium">
      <Card variation="elevated" padding="medium">
        <Flex direction="column" gap="medium">
          <Heading level={3}>Enter Job Name</Heading>
          <form onSubmit={handleSubmitJobName}>
            <Flex direction="row" gap="medium" alignItems="end">
              <TextField
                label="Job Name"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                placeholder="Enter job name"
                required
              />
              <Button type="submit" variation="primary">
                Submit
              </Button>
            </Flex>
          </form>
        </Flex>
      </Card>
  
      {submittedJobName && (
        <>
          {jobs.size > 0 && Array.from(jobs.values()).map(job => (
            <Card 
              key={job.job_name}
              variation="elevated"
              padding="medium"
              marginTop="medium"
            >
              <Flex direction="column" gap="medium">
                <Flex justifyContent="space-between" alignItems="center">
                  <Heading level={4}>Job: {job.job_name}</Heading>
                  <Text>Type: {job.job_type}</Text>
                </Flex>

                <Flex direction="row" gap="large" justifyContent="space-around">
                  <Card variation="outlined" padding="medium">
                    <Flex direction="column" alignItems="center" gap="small">
                      <Heading level={5}>In Queue</Heading>
                      <Text fontSize="xx-large">
                        {job.works.filter(w => w.status === 'IN_QUEUE').length}
                      </Text>
                    </Flex>
                  </Card>

                  <Card variation="outlined" padding="medium">
                    <Flex direction="column" alignItems="center" gap="small">
                      <Heading level={5}>In Progress</Heading>
                      <Text fontSize="xx-large">
                        {job.works.filter(w => w.status === 'IN_PROGRESS').length}
                      </Text>
                    </Flex>
                  </Card>

                  <Card variation="outlined" padding="medium">
                    <Flex direction="column" alignItems="center" gap="small">
                      <Heading level={5}>Completed</Heading>
                      <Text fontSize="xx-large">
                        {job.works.filter(w => w.status === 'READY FOR REVIEW').length}
                      </Text>
                    </Flex>
                  </Card>

                  <Card 
                    variation="outlined" 
                    padding="medium"
                    backgroundColor={job.works.some(w => w.status === 'FAILED TO PROCESS') ? '#fff1f1' : undefined}
                  >
                    <Flex direction="column" alignItems="center" gap="small">
                      <Heading level={5}>Failed</Heading>
                      <Text 
                        fontSize="xx-large"
                        color={job.works.some(w => w.status === 'FAILED TO PROCESS') ? 'red' : undefined}
                      >
                        {job.works.filter(w => w.status === 'FAILED TO PROCESS').length}
                      </Text>
                    </Flex>
                  </Card>
                </Flex>

                <Flex direction="column" gap="medium">
                  <progress 
                    value={
                      (job.works.filter(w => w.status === 'READY FOR REVIEW').length / job.works.length) * 100
                    } 
                    max="100"
                    style={{ width: '100%', height: '20px' }}
                  />
                  <Text textAlign="center">
                    Overall Progress: {Math.round((job.works.filter(w => w.status === 'READY FOR REVIEW').length / job.works.length) * 100)}%
                  </Text>
                </Flex>

                {job.works.some(w => w.status === 'READY FOR REVIEW') && (
                  <Flex justifyContent="center">
                    <Button
                      variation="primary"
                      onClick={() => handleViewResults(job, job.works[0])}
                      size="large"
                    >
                      View Results
                    </Button>
                  </Flex>
                )}
              </Flex>
            </Card>
          ))}
  
          {isLoading && (
            <Flex direction="column" alignItems="center" padding="large">
              <Loader size="large" />
              <Text>Loading jobs...</Text>
            </Flex>
          )}
  
          {error && (
            <Alert variation="error">
              {error}
            </Alert>
          )}
  
          {jobs.size === 0 && !isLoading && (
            <Card variation="elevated" marginTop="medium">
              <Text>No active jobs found for {submittedJobName}</Text>
            </Card>
          )}
        </>
      )}
    </View>
  );
};

export default JobStatus;