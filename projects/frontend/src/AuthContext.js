/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { createContext, useState, useContext } from 'react';

const AuthContext = createContext(null);

// Inside AuthContext.js
export const AuthProvider = ({ children }) => {
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey'));

  const login = (newApiKey) => {
    localStorage.setItem('apiKey', newApiKey);
    setApiKey(newApiKey);
  };

  const logout = () => {
    localStorage.removeItem('apiKey');
    setApiKey(null);
  };

  // Add this function to use in your API calls
  const getAuthHeaders = () => {
    return apiKey ? { 'x-api-key': apiKey } : {};
  };

  return (
    <AuthContext.Provider value={{ apiKey, login, logout, isAuthenticated: !!apiKey, getAuthHeaders }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
