/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import { useCallback } from 'react';
import { formatValue} from "../utils/formatter";

export default function useMetadataUpdate({
  token, logout, navigate, setError, setIsLoading,
  selectedWork, metadata, modifiedFields, setModifiedFields, setMetadata,
  allWorks, fetchWorkDetails
}) {

  const updateMetadata = useCallback(async () => {
    if (!token || !selectedWork) {
      setError('Unable to update: Missing required data');
      return;
    }

    try {
      setIsLoading(true);
      const processedModifiedFields = {};

      Object.entries(modifiedFields).forEach(([key, value]) => {
        if (typeof value === 'object' && value !== null && 'value' in value) {
          if (typeof value.value === 'string') {
            processedModifiedFields[key] = {
              ...value,
              value: value.value.includes(',') ?
                value.value.split(',').map(item => item.trim()) :
                value.value
            };
          } else {
            processedModifiedFields[key] = value;
          }
        } else if (typeof value === 'string' &&
                  metadata[key] &&
                  typeof metadata[key] === 'object' &&
                  Array.isArray(metadata[key].value)) {
          processedModifiedFields[key] = {
            ...metadata[key],
            value: value.includes(',') ?
              value.split(',').map(item => item.trim()) :
              [value]
          };
        } else {
          processedModifiedFields[key] = value;
        }
      });

      console.log("Sending update with fields:", processedModifiedFields);

      const url = `/api/results`;
      const requestBody = {
        job_name: selectedWork.job_name,
        work_id: selectedWork.work_id,
        updated_fields: processedModifiedFields
      };

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          throw new Error('Authentication failed. Please log in again.');
        }

        const errorText = await response.text();
        console.error('API Error Response:', JSON.stringify(errorText));
        throw new Error(`Failed to update metadata: ${response.status}`);
      }

      const data = await response.json();
      setMetadata(data.item);
      setModifiedFields({});
      setError(null);
    } catch (err) {
      console.error('Error updating metadata:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [token, logout, navigate, selectedWork, metadata, modifiedFields, setError, setIsLoading, setModifiedFields, setMetadata]);

  const downloadAllMetadata = useCallback(async () => {
    if (!allWorks || allWorks.length === 0 || !token) {
      console.error('No works available or not authenticated to download metadata.');
      return;
    }

    try {
      setIsLoading(true);
      const allMetadataResults = [];
      const currentJobName = selectedWork?.job_name || allWorks[0]?.job_name;

      if (!currentJobName) {
        throw new Error('Job name is undefined. Please select a work first.');
      }

      for (let i = 0; i < allWorks.length; i++) {
        const work = allWorks[i];
        try {
          const metadata = await fetchWorkDetails(work.work_id, work.job_name);
          allMetadataResults.push({
            ...metadata,
            work_id: work.work_id,
            work_status: work.work_status
          });
        } catch (err) {
          console.error(`Error fetching work ${work.work_id}:`, err);
          allMetadataResults.push({
            work_id: work.work_id,
            work_status: 'ERROR',
            error: 'Failed to fetch metadata'
          });
        }
      }

      const headers = ['work_id', 'work_status'];
      const metadataKeys = new Set();
      allMetadataResults.forEach(metadata => {
        Object.keys(metadata).forEach(key => {
          if (!['work_id', 'work_status', 'image_s3_uris'].includes(key)) {
            metadataKeys.add(key);
          }
        });
      });
      headers.push(...Array.from(metadataKeys));

      const rows = allMetadataResults.map(metadata => {
        return headers.map(header => {
          const value = metadata[header];
          if (!value) return '""';
          if (typeof value === 'object' && value !== null) {
            if ('explanation' in value && 'value' in value) {
              return `"${formatValue(value.value)} (${value.explanation.replace(/"/g, '""')})"`;
            }
            return `"${formatValue(value).replace(/"/g, '""')}"`;
          }
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',');
      });

      const csvContent = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${currentJobName}-all-results-${new Date().toISOString()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      setError(null);
    } catch (error) {
      console.error('Error downloading all metadata:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  }, [allWorks, token, selectedWork, fetchWorkDetails, setError, setIsLoading]);

  return { updateMetadata, downloadAllMetadata };
}
