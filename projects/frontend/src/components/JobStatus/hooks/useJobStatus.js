/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

// components/JobStatus/hooks/useJobStatus.js

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../AuthContext';
import { buildApiUrl } from '../../../utils/apiUrls';

const useJobStatus = (token, navigate) => {
  const { logout } = useAuth();
  const [jobs, setJobs] = useState(() => {
    const savedJobs = localStorage.getItem('jobStatus');
    return savedJobs ? new Map(JSON.parse(savedJobs)) : new Map();
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [submittedJobName, setSubmittedJobName] = useState(() => {
    return localStorage.getItem('submittedJobName') || '';
  });

  useEffect(() => {
    localStorage.setItem('jobStatus', JSON.stringify(Array.from(jobs.entries())));
  }, [jobs]);

  useEffect(() => {
    localStorage.setItem('submittedJobName', submittedJobName);

    // Clear existing jobs when job name changes
    if (submittedJobName) {
      setJobs(new Map());
      setError(null);
    }
  }, [submittedJobName]);
  const { getAuthHeaders } = useAuth();
  const checkJobProgress = useCallback(async () => {
    if (!token || !submittedJobName) return;

    try {
      setIsLoading(true);
      const url = buildApiUrl('/api/job_progress');
      console.log(`Fetching from: ${url}?job_name=${submittedJobName}`);
      const response = await fetch(
        `${url}?job_name=${submittedJobName}`,
        {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json'
          }
        }
      );

      console.log('Response Status:', response.status);
      const responseText = await response.text();
      console.log('Response Body:', responseText);

      if (!response.ok) {
        // Handle unauthorized responses (token expired)
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          return;
        }

        setJobs(new Map());
        return;
      }

      // Parse JSON after logging the raw text
      let data;
      try {
        data = JSON.parse(responseText);
        console.log('Parsed Data:', data);
      } catch (parseError) {
        console.error('JSON Parse Error:', parseError);
        return;
      }

      const newJobs = new Map();
      const jobKey = submittedJobName;
      const workItems = [];

      if (data && data.job_progress) {
        console.log('Job progress structure:', data.job_progress);
        Object.entries(data.job_progress).forEach(([work_status, ids]) => {
          // Check if ids is an array before processing
          if (Array.isArray(ids)) {
            ids.forEach(id => {
              workItems.push({
                work_id: id,
                work_status: work_status,
                job_name: jobKey,
                job_type: data.job_type || 'unknown'
              });
            });
          } else {
            console.warn(`Expected array for work_status "${work_status}" but got:`, ids);
          }
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
      setError('Failed to fetch job progress. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [token, submittedJobName, logout, navigate, getAuthHeaders]);

  useEffect(() => {
    if (token && submittedJobName) {
      checkJobProgress();
    }
  }, [token, submittedJobName, checkJobProgress]);

  return {
    jobs,
    setJobs,
    isLoading,
    error,
    submittedJobName,
    setSubmittedJobName,
    checkJobProgress
  };
};

export default useJobStatus;
