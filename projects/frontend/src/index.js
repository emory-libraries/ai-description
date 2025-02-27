import React from 'react';
import ReactDOM from 'react-dom';
import { AuthProvider } from "react-oidc-context";
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import JobStatus from './JobStatus';
import Metadata from './Metadata';  
import Bias from './Bias';
import { createRoot } from 'react-dom/client';

const cognitoAuthConfig = {
  authority: process.env.REACT_APP_COGNITO_AUTHORITY,
  client_id: process.env.REACT_APP_COGNITO_CLIENT_ID,
  redirect_uri: process.env.REACT_APP_COGNITO_REDIRECT_URI,
  response_type: "code",
  scope: "email openid phone",
};

console.log('Cognito Config:', {
  authority: process.env.REACT_APP_COGNITO_AUTHORITY,
  client_id: process.env.REACT_APP_COGNITO_CLIENT_ID,
  redirect_uri: process.env.REACT_APP_COGNITO_REDIRECT_URI
});

const root = createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <AuthProvider {...cognitoAuthConfig}>
      <Router>
        <Routes>
          <Route path="/" element={<JobStatus />} />
          <Route 
            path="/results/metadata/:jobName" 
            element={<Metadata />}
          />
          <Route 
            path="/results/bias/:jobName" 
            element={<Bias />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  </React.StrictMode>,
  document.getElementById('root')
);