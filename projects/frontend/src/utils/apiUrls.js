/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// src/utils/apiUrls.js

export const getApiBaseUrl = () => {
  return window.env?.API_URL || 'https://api-url-not-configured.example';
};

export const buildApiUrl = (endpoint) => {
  const baseUrl = getApiBaseUrl();
  const formattedEndpoint = endpoint ? (endpoint.startsWith('/') ? endpoint : `/${endpoint}`) : '';
  return `${baseUrl}${formattedEndpoint}`;
};
