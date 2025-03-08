/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../AuthContext';
import useMetadataFetch from './hooks/useMetadataFetch';
import useMetadataUpdate from './hooks/useMetadataUpdate';
import useImageLoader from './hooks/useImageLoader';

const MetadataContext = createContext();

export const useMetadataContext = () => useContext(MetadataContext);

export function MetadataProvider({ children }) {
  const { token, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { jobName, workId } = location.state || {};

  const [selectedWork, setSelectedWork] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState({});
  const [modifiedFields, setModifiedFields] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [allWorks, setAllWorks] = useState([]);

  const { fetchWorkDetails, fetchAllWorks } = useMetadataFetch({
    token,
    logout,
    navigate,
    setError
  });

  const { getPresignedUrl } = useImageLoader({ token, logout, navigate });

  const { updateMetadata, downloadAllMetadata } = useMetadataUpdate({
    token,
    logout,
    navigate,
    setError,
    setIsLoading,
    selectedWork,
    metadata,
    modifiedFields,
    setModifiedFields,
    setMetadata,
    allWorks,
    fetchWorkDetails
  });

  const handleMetadataEdit = (key, value) => {
    if (key === 'job_name' || key === 'work_id') return;

    let processedValue = value;
    if (typeof value === 'object' && value !== null && 'value' in value) {
      processedValue = { ...value };
    }

    setMetadata(prev => ({
      ...prev,
      [key]: processedValue
    }));

    setModifiedFields(prev => ({
      ...prev,
      [key]: processedValue
    }));
  };

  const handleWorkSelect = async (work) => {
    setIsLoading(true);
    setSelectedWork(work);
    setMetadata(null);
    setImageData({});
    setError(null);
    setModifiedFields({});

    try {
      const workDetails = await fetchWorkDetails(work.work_id, work.job_name);
      setMetadata(workDetails);

      if (workDetails.image_s3_uris && workDetails.image_s3_uris.length > 0) {
        const imagePromises = workDetails.image_s3_uris.map(async uri => {
          const imageUrl = await getPresignedUrl(uri);
          return { uri, imageUrl };
        });

        const images = await Promise.all(imagePromises);
        const newImageData = {};
        images.forEach(({ uri, imageUrl }) => {
          if (imageUrl) newImageData[uri] = imageUrl;
        });

        setImageData(newImageData);
      }
    } catch (err) {
      console.error('Error in handleWorkSelect:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    async function loadInitialData() {
      if (!token || !jobName) return;

      try {
        setIsLoading(true);
        const works = await fetchAllWorks(jobName);
        setAllWorks(works);

        if (workId) {
          const workToSelect = works.find(w => w.work_id === workId);
          if (workToSelect) {
            await handleWorkSelect(workToSelect);
          } else if (works.length > 0) {
            await handleWorkSelect(works[0]);
          }
        } else if (works.length > 0) {
          await handleWorkSelect(works[0]);
        }
      } catch (err) {
        console.error('Error loading initial data:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    }

    loadInitialData();
  }, [token, jobName, workId]);

  const contextValue = {
    token,
    jobName,
    selectedWork,
    metadata,
    error,
    imageData,
    modifiedFields,
    isLoading,
    allWorks,
    setSelectedWork,
    handleWorkSelect,
    handleMetadataEdit,
    updateMetadata,
    downloadAllMetadata
  };

  return (
    <MetadataContext.Provider value={contextValue}>
      {children}
    </MetadataContext.Provider>
  );
}
