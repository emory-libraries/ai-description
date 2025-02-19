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

const API_ENDPOINT = 'https://snqamgfnv4.execute-api.us-east-1.amazonaws.com/dev';

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
    if (jobName.trim()) {
      setJobs(new Map());
      setError(null);
      setSubmittedJobName(jobName.trim());
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
            'Authorization': `Bearer ${auth.user.access_token}`,
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
      console.log('Job Progress Data:', data);
  
      const newJobs = new Map();
      const jobKey = submittedJobName;
  
      const workItems = [
        ...(data['READY FOR REVIEW'] || []).map(id => ({ 
          work_id: id,
          status: 'READY FOR REVIEW',
          job_name: jobKey,
        })),
        ...(data['IN_PROGRESS'] || []).map(id => ({ 
          work_id: id,
          status: 'IN_PROGRESS',
          job_name: jobKey,
        })),
        ...(data['IN_QUEUE'] || []).map(id => ({ 
          work_id: id,
          status: 'IN_QUEUE',
          job_name: jobKey,
        }))
      ];
  
      const jobData = {
        job_name: jobKey,
        works: workItems,
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
      workId: work.work_id
    });

    navigate(`/results/${job.job_name}`, { 
      state: { 
        jobName: job.job_name,
        workId: work.work_id
      }
    });
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
            <Collection
              key={job.job_name}
              type="list"
              items={job.works}
              gap="medium"
            >
              {(work) => (
                <Card 
                  key={work.work_id}
                  variation="elevated"
                  padding="medium"
                >
                  <Flex direction="column" gap="small">
                    <Text>Job Name: {work.job_name}</Text>
                    <Text>Work ID: {work.work_id}</Text>
                    <Text>Status: {work.status}</Text>
                    
                    <Flex direction="column" gap="xs">
                      <Text>Completed: {work.status === 'READY FOR REVIEW' ? 1 : 0}</Text>
                      <Text>In Progress: {work.status === 'IN_PROGRESS' ? 1 : 0}</Text>
                      <Text>In Queue: {work.status === 'IN_QUEUE' ? 1 : 0}</Text>
                      <progress 
                        value={work.status === 'READY FOR REVIEW' ? 100 : 
                              work.status === 'IN_PROGRESS' ? 50 : 0} 
                        max="100" 
                      />
                      <Text>
                        {work.status === 'READY FOR REVIEW' ? '100' : 
                        work.status === 'IN_PROGRESS' ? '50' : '0'}%
                      </Text>
                    </Flex>

                    {work.status === 'READY FOR REVIEW' && (
                      <Button
                        variation="primary"
                        onClick={() => handleViewResults(job, work)}
                      >
                        View Results
                      </Button>
                    )}
                  </Flex>
                </Card>
              )}
            </Collection>
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
            <Card variation="elevated">
              <Text>No active jobs found for {submittedJobName}</Text>
            </Card>
          )}
        </>
      )}
    </View>
  );
};

export default JobStatus;