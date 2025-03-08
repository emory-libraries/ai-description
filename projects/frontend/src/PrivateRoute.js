/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

const PrivateRoute = ({ children }) => {
  const { token } = useAuth();
  console.log("PrivateRoute check - token exists:", !!token);
  return token ? children : <Navigate to="/login" />;
};

export default PrivateRoute;
