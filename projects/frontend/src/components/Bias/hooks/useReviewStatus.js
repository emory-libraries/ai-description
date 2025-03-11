/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// components/Bias/hooks/useReviewStatus.js

import { useCallback, useState } from 'react';
import { useAuth } from '../../../AuthContext';
import { useNavigate } from 'react-router-dom';
import { buildApiUrl } from '../../../utils/apiUrls';

export function useReviewStatus({ setAllWorks, setSelectedWork, selectedWork }) {
  const [isUpdatingReviewStatus, setIsUpdatingReviewStatus] = useState(false);
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const updateReviewStatus = useCallback(
    async (work, newStatus) => {
      if (!work || !token) {
        console.error('Unable to update: Missing work data or authentication');
        return;
      }

      try {
        setIsUpdatingReviewStatus(true);

        const url = buildApiUrl(`/api/results`);
        const response = await fetch(url, {
          method: 'PUT',
          headers: {
            'x-api-key': token,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            job_name: work.job_name,
            work_id: work.work_id,
            updated_fields: { work_status: newStatus },
          }),
        });

        if (!response.ok) {
          if (response.status === 401 || response.status === 403) {
            logout();
            navigate('/login');
            throw new Error('Authentication failed. Please log in again.');
          }

          const errorText = await response.text();
          console.error('API Error Response:', errorText);
          throw new Error(`Failed to update work status: ${response.status}`);
        }

        const updatedWork = await response.json();

        // Update the work in allWorks
        setAllWorks((prevWorks) =>
          prevWorks.map((w) => (w.work_id === work.work_id ? { ...w, work_status: newStatus } : w)),
        );

        // Update the selectedWork if it's the one being updated
        if (selectedWork && selectedWork.work_id === work.work_id) {
          setSelectedWork({ ...selectedWork, work_status: newStatus });
        }

        return updatedWork;
      } catch (err) {
        console.error(`Error updating work status to ${newStatus}:`, err);
        throw err;
      } finally {
        setIsUpdatingReviewStatus(false);
      }
    },
    [token, logout, navigate, selectedWork, setAllWorks, setSelectedWork],
  );

  return { updateReviewStatus, isUpdatingReviewStatus };
}
