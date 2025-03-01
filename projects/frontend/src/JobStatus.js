/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  View,
  Card,
  Button,
  Heading,
  Flex,
  Text,
  Alert,
  Loader,
  Collection
} from '@aws-amplify/ui-react';

const mockDynamoDB = {
  jobs: new Map([
    ['job_1', {
      job_name: 'yearbook',
      work_id: '5',
      s3_uris: ['s3://emory-testui/test/Charlie Chaplin.jpg', 's3://emory-testui/test/Eddie Anderson.jpg'],
      work_status: 100,
      description: 'yearbook collection run'
    }],
    ['job_2', {
      job_name: 'Langmuir',
      work_id: '5',
      s3_uris: ['s3://emory-testui/test/Charlie Chaplin.jpg', 's3://emory-testui/test/Eddie Anderson.jpg'],
      work_status: 50,
      description: 'langmuir collection run'
    }]
  ])
};

const JobStatus = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const mockJobStatusLambda = async (event) => {
    await new Promise(resolve => setTimeout(resolve, 200));

    switch (event.action) {
      case 'getStatus':
        return mockDynamoDB.jobs.get(event.jobId);
      case 'listJobs':
        return Array.from(mockDynamoDB.jobs.values());
      default:
        throw new Error('Invalid action');
    }
  };

  const pollJobStatus = async () => {
    try {
      setIsLoading(true);
      const results = await mockJobStatusLambda({
        action: 'listJobs'
      });
      setJobs(results);
    } catch (err) {
      setError('Failed to fetch jobs');
      console.error('Error polling jobs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const interval = setInterval(pollJobStatus, 5000);
    pollJobStatus(); // Initial poll
    return () => clearInterval(interval);
  }, []);

  const handleViewResults = (job) => {
    navigate(`/results/\${job.job_name}`, {
      state: {
        s3Uris: job.s3_uris,
        jobName: job.job_name
      }
    });
  };

  return (
    <View padding="medium">
      <Card variation="elevated">
        <Flex direction="column" gap="medium">
          <Heading level={4}>Jobs</Heading>

          {error && <Alert variation="error">{error}</Alert>}

          {isLoading ? (
            <Flex direction="column" alignItems="center">
              <Loader size="large" />
              <Text>Loading jobs...</Text>
            </Flex>
          ) : (
            <Collection
              type="list"
              items={jobs}
              gap="small"
            >
              {(job) => (
                <Card key={job.job_name} variation="outlined">
                  <Flex direction="column" gap="small">
                    <Text>Job Name: {job.job_name}</Text>
                    <Text>Work Id: {job.work_id}</Text>
                    <Text>Description: {job.description}</Text>
                    {job.work_status !== undefined && (
                      <Flex direction="column" gap="xs">
                        <progress value={job.work_status} max="100" />
                        <Text>{job.work_status}%</Text>
                      </Flex>
                    )}
                    {job.work_status === 100 && (
                      <Button
                        variation="primary"
                        onClick={() => handleViewResults(job)}
                      >
                        View Results
                      </Button>
                    )}
                  </Flex>
                </Card>
              )}
            </Collection>
          )}
        </Flex>
      </Card>
    </View>
  );
};

export default JobStatus;
