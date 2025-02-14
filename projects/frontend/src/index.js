/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import ReactDOM from 'react-dom';
import { AuthProvider } from "react-oidc-context";
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import JobStatus from './JobStatus';
import App from './App';

const cognitoAuthConfig = {
  authority: process.env.REACT_APP_COGNITO_AUTHORITY,
  client_id: process.env.REACT_APP_COGNITO_CLIENT_ID,
  redirect_uri: process.env.REACT_APP_COGNITO_REDIRECT_URI,
  response_type: "code",
  scope: "email openid phone",
};

ReactDOM.render(
  <React.StrictMode>
    <AuthProvider {...cognitoAuthConfig}>
      <Router>
        <Routes>
          <Route path="/" element={<JobStatus />} />
          <Route
            path="/results/:jobName"
            element={<App />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  </React.StrictMode>,
  document.getElementById('root')
);
