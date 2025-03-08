// src/utils/apiUrls.js

export const getApiBaseUrl = () => {
    return window.env?.API_URL || 'https://91vt697st6.execute-api.us-east-1.amazonaws.com/dev';
  };
  
  export const buildApiUrl = (endpoint) => {
    const baseUrl = getApiBaseUrl();
    const formattedEndpoint = endpoint ? (endpoint.startsWith('/') ? endpoint : `/${endpoint}`) : '';
    return `${baseUrl}${formattedEndpoint}`;
  };