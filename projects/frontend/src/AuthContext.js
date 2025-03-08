/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

// AuthContext.js

import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext();
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  // Use localStorage to persist the token between page refreshes
  const [token, setToken] = useState(localStorage.getItem('apiKey'));
  
  const login = (apiKey) => {
    // Store token in both state and localStorage
    localStorage.setItem('apiKey', apiKey);
    setToken(apiKey);
  };
  
  const logout = () => {
    localStorage.removeItem('apiKey');
    setToken(null);
  };
  
  const getAuthHeaders = () => {
    return token ? { 'x-api-key': token } : {};
  };
  
  return (
    <AuthContext.Provider value={{ token, login, logout, getAuthHeaders }}>
      {children}
    </AuthContext.Provider>
  );
};

