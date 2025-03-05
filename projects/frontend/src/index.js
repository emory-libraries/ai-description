/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import JobStatus from './JobStatus';
import Metadata from './Metadata';
import Bias from './Bias';
import "@cloudscape-design/global-styles/index.css";
import { applyMode, Mode } from '@cloudscape-design/global-styles';
import { AuthProvider } from './AuthContext';
import Login from './Login';

applyMode(Mode.Dark);

const root = createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
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
  </React.StrictMode>
);
