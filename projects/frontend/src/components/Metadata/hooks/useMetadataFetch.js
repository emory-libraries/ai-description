import { useCallback } from 'react';

export default function useMetadataFetch({ token, logout, navigate, setError }) {
  const fetchWorkDetails = useCallback(async (workId, jobName) => {
    if (!token) return;
    
    try {
      const response = await fetch(
        `/api/results?job_name=${jobName}&work_id=${workId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`Failed to fetch work details: ${response.status}`);
      }

      const data = await response.json();
      return data.item;
    } catch (err) {
      console.error('Error fetching work details:', err);
      throw err;
    }
  }, [token, logout, navigate]);

  const fetchAllWorks = useCallback(async (jobName) => {
    if (!token || !jobName) return [];
    
    try {
      const response = await fetch(
        `/api/job_progress?job_name=${jobName}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`Failed to fetch job data: ${response.status}`);
      }

      const jobData = await response.json();
      const works = [];

      if (jobData.job_progress) {
        Object.entries(jobData.job_progress).forEach(([status, ids]) => {
          ids.forEach(id => {
            works.push({
              work_id: id,
              work_status: status,
              job_name: jobName,
              job_type: jobData.job_type
            });
          });
        });
      }

      return works;
    } catch (err) {
      console.error('Error fetching all works:', err);
      setError(err.message);
      return [];
    }
  }, [token, logout, navigate, setError]);

  return { fetchWorkDetails, fetchAllWorks };
}
