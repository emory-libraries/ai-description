/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// components/Bias/BiasContext.js

import React, { createContext, useContext } from 'react';
import { useWorkData } from './hooks/useWorkData';
import { useBiasData } from './hooks/useBiasData';
import { useLocation, useNavigate } from 'react-router-dom';
import { buildFrontendPath } from '../../utils/frontendPaths';
import { useReviewStatus } from './hooks/useReviewStatus'; // Add this import

const BiasContext = createContext(null);

export function BiasProvider({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { jobName: stateJobName } = location.state || {};

  // Extract jobName from URL path - improved extraction
  // Look for 'bias' in the path segments and take the next segment as jobName
  const pathMatch = location.pathname.match(/\/results\/bias\/([^/]+)/);
  const pathJobName = pathMatch ? pathMatch[1] : '';

  // Extract workId from hash fragment - improved parsing
  // The workId is expected to be after the '#' character
  const hashWorkId = location.hash.substring(1);

  // Use the most specific information available
  const jobName = stateJobName || pathJobName;
  const workId = location.state?.workId || hashWorkId;

  const navigateToJobs = () => navigate(buildFrontendPath('/'));

  // Bias data state management
  const {
    biasData,
    error: biasError,
    imageData,
    isLoading: biasLoading,
    selectedBias,
    loadBiasData,
    handleBiasSelect,
    handleBackToBiasList,
  } = useBiasData(jobName);

  // Work data state management
  const {
    allWorks,
    selectedWork,
    isLoading: worksLoading,
    error: worksError,
    handleWorkSelect,
    setAllWorks,
    setSelectedWork,
  } = useWorkData(jobName, workId, loadBiasData);

  // Review status management
  const { updateReviewStatus, isUpdatingReviewStatus } = useReviewStatus({
    setAllWorks,
    setSelectedWork,
    selectedWork,
  });

  const error = biasError || worksError;
  const isLoading = biasLoading || worksLoading || isUpdatingReviewStatus;

  // Combined context value
  const contextValue = {
    // Bias data
    biasData,
    imageData,
    selectedBias,
    handleBiasSelect,
    handleBackToBiasList,

    // Work data
    allWorks,
    selectedWork,
    handleWorkSelect,

    // Review status
    updateReviewStatus,

    // Status
    jobName,
    workId,
    error,
    isLoading,
    navigateToJobs,
  };

  return <BiasContext.Provider value={contextValue}>{children}</BiasContext.Provider>;
}

export const useBiasContext = () => {
  const context = useContext(BiasContext);
  if (!context) {
    throw new Error('useBiasContext must be used within a BiasProvider');
  }
  return context;
};
