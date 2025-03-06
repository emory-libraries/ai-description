import { useCallback } from 'react';

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
      
      const response = await fetch(
        `/api/presigned_url?s3_uri=${encodeURIComponent(s3Uri)}`,
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