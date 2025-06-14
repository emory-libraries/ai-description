/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */
import { useCallback } from 'react';
import { buildApiUrl } from '../../../utils/apiUrls';
import { useAuth } from '../../../AuthContext';

export default function useMetadataFetch({ token, logout, navigate, setError }) {
  const { getAuthHeaders } = useAuth();

  const fetchWorkDetails = useCallback(
    async (workId, jobName) => {
      if (!token) return;

      try {
        const url = buildApiUrl(`/api/results?job_name=${jobName}&work_id=${workId}`);
        const response = await fetch(url, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
        });

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
    },
    [token, logout, navigate, getAuthHeaders],
  );

  const fetchAllWorks = useCallback(
    async (jobName) => {
      if (!token || !jobName) return [];

      try {
        const url = buildApiUrl(`/api/job_progress?job_name=${jobName}`);
        const response = await fetch(url, {
          headers: {
            ...getAuthHeaders(),
            'Content-Type': 'application/json',
          },
        });

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
            ids.forEach((id) => {
              works.push({
                work_id: id,
                work_status: status,
                job_name: jobName,
                job_type: jobData.job_type,
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
    },
    [token, logout, navigate, setError, getAuthHeaders],
  );

  return { fetchWorkDetails, fetchAllWorks };
}
