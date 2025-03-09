/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// src/utils/frontendPaths.js

export const getFrontendBasePath = () => {
  return window.env?.STAGE_NAME || '/dev';
};

export const buildFrontendPath = (endpoint) => {
  const basePath = getFrontendBasePath();
  const formattedEndpoint = endpoint ? (endpoint.startsWith('/') ? endpoint : `/${endpoint}`) : '';
  return `${basePath}${formattedEndpoint}`;
};
