/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../../AuthContext';
import { useNavigate } from 'react-router-dom';
import { buildApiUrl } from '../../../utils/apiUrls';

// components/Bias/hooks/useWorkData.js

/**
 * Hook to handle work data fetching and selection
 */
export const useWorkData = (jobName, initialWorkId, onWorkSelect) => {
  const navigate = useNavigate();
  const { token, logout } = useAuth();

  const [allWorks, setAllWorks] = useState([]);
  const [selectedWork, setSelectedWork] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleWorkSelect = useCallback(
    (work) => {
      if (!work) return;

      setSelectedWork(work);
      onWorkSelect(work);
    },
    [onWorkSelect],
  );

  useEffect(() => {
    const fetchAllWorks = async () => {
      if (!token || !jobName) return;

      try {
        setIsLoading(true);
        // Instead of calling useAuth() inside this function,
        // use the token and headers you already have from the parent scope
        const url = buildApiUrl(`/api/job_progress?job_name=${jobName}`);
        const response = await fetch(url, {
          headers: {
            'x-api-key': token,
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
          Object.entries(jobData.job_progress).forEach(([work_status, ids]) => {
            ids.forEach((id) => {
              works.push({
                work_id: id,
                work_status: work_status,
                job_name: jobName,
                job_type: jobData.job_type,
              });
            });
          });
        }

        setAllWorks(works);

        if (initialWorkId) {
          const workToSelect = works.find((w) => w.work_id === initialWorkId);
          if (workToSelect) {
            await handleWorkSelect(workToSelect);
          }
        } else if (works.length > 0) {
          await handleWorkSelect(works[0]);
        }
      } catch (err) {
        console.error('Error fetching all works:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (token && jobName) {
      fetchAllWorks();
    }
  }, [token, jobName, initialWorkId, handleWorkSelect, logout, navigate]);

  // Include these setters in the return value
  return {
    allWorks,
    selectedWork,
    isLoading,
    error,
    handleWorkSelect,
    setAllWorks,
    setSelectedWork,
  };
};
