/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */
import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../AuthContext';
import { usePresignedUrl } from './usePresignedUrl';
import { buildApiUrl } from '../../../utils/apiUrls';

/**
 * Hook to handle bias data fetching and management
 */
export const useBiasData = (jobName) => {
  const navigate = useNavigate();
  const { getPresignedUrl } = usePresignedUrl();

  const [biasData, setBiasData] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [selectedBias, setSelectedBias] = useState(null);
  const { token, logout, getAuthHeaders } = useAuth();

  const fetchBiasDetails = useCallback(
    async (workId) => {
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
          throw new Error(`Failed to fetch bias details: ${response.status}`);
        }

        const data = await response.json();

        // Handle case where work processing failed or data is missing
        if (!data.item || !data.item.page_biases || data.item.status === 'FAILED TO PROCESS') {
          return { biases: [], image_s3_uris: [], status: data.item?.status || 'FAILED TO PROCESS' };
        }

        const biasEntriesWithImages = data.item.page_biases.flatMap((page, pageIndex) =>
          page.biases.map((bias) => ({
            ...bias,
            bias_type: bias.type,
            bias_level: bias.level,
            pageNumber: pageIndex + 1,
            imageUri: data.item.image_s3_uris[pageIndex],
          })),
        );
        return {
          biases: biasEntriesWithImages,
          image_s3_uris: data.item.image_s3_uris,
          status: data.item.status,
        };
      } catch (err) {
        console.error('Error fetching bias details:', err);
        throw err;
      }
    },
    [jobName, token, logout, navigate, getAuthHeaders],
  );

  const loadBiasData = useCallback(
    async (work) => {
      if (!work) return;

      setIsLoading(true);
      setSelectedBias(null);
      setBiasData(null);
      setError(null);
      setImageData({});

      try {
        if (!token) {
          throw new Error('No authentication token available');
        }

        // Check if the work has failed status before fetching details
        if (work.work_status === 'FAILED TO PROCESS') {
          setBiasData([]);
          return;
        }

        const { biases, image_s3_uris, status } = await fetchBiasDetails(work.work_id);

        // Handle failed work or missing data after fetch
        if (status === 'FAILED' || !biases || biases.length === 0) {
          setBiasData([]);
          return;
        }

        setBiasData(biases);

        if (image_s3_uris && image_s3_uris.length > 0) {
          const imagePromises = image_s3_uris.map(async (uri) => {
            try {
              const presignedUrl = await getPresignedUrl(uri);
              return { uri, imageUrl: presignedUrl };
            } catch (err) {
              console.error(`Failed to get presigned URL for ${uri}`, err);
              return { uri, imageUrl: null };
            }
          });
          const images = await Promise.all(imagePromises);
          const newImageData = {};
          images.forEach(({ uri, imageUrl }) => {
            if (imageUrl) newImageData[uri] = imageUrl;
          });
          setImageData(newImageData);
        }
      } catch (err) {
        console.error('Error in loadBiasData:', err);
        setError(err.message);
        setBiasData([]); // Set empty array so UI can render properly
      } finally {
        setIsLoading(false);
      }
    },
    [fetchBiasDetails, getPresignedUrl, token],
  );

  const handleBiasSelect = (biasEntry) => {
    setSelectedBias(biasEntry);
  };

  const handleBackToBiasList = () => {
    setSelectedBias(null);
  };

  return {
    biasData,
    error,
    imageData,
    isLoading,
    selectedBias,
    loadBiasData,
    handleBiasSelect,
    handleBackToBiasList,
  };
};
