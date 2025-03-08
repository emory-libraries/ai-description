/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import { useCallback } from 'react';
import { buildApiUrl } from './utils/apiUrls';

export default function useImageLoader({ token, logout, navigate }) {
  const getPresignedUrl = useCallback(async (s3Uri) => {
    if (!s3Uri || typeof s3Uri !== 'string') {
      console.error('Invalid URI provided:', s3Uri);
      return null;
    }

    try {
      if (!token) {
        throw new Error('No authentication token available');
      }
      const url = buildApiUrl(`/api/presigned_url?s3_uri=${encodeURIComponent(s3Uri)}`);
      const response = await fetch(
        url,
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
        throw new Error(`Failed to get pre-signed URL: ${response.status}`);
      }

      const data = await response.json();
      return data.presigned_url;
    } catch (err) {
      console.error('Error getting pre-signed URL:', err);
      return null;
    }
  }, [token, logout, navigate]);

  return { getPresignedUrl };
}
