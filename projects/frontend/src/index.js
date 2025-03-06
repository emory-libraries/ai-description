/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import JobStatus from './components/JobStatus';
import Metadata from './components/Metadata';
import Bias from './components/Bias';
import "@cloudscape-design/global-styles/index.css";
import { applyMode, Mode } from '@cloudscape-design/global-styles';
import { AuthProvider } from './AuthContext';
import Login from './Login';
import PrivateRoute from './PrivateRoute'

applyMode(Mode.Dark);

const root = createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateRoute><JobStatus /></PrivateRoute>} />
          <Route
            path="/results/metadata/:jobName"
            element={<PrivateRoute><Metadata /></PrivateRoute>}
          />
          <Route
            path="/results/bias/:jobName"
            element={<PrivateRoute><Bias /></PrivateRoute>}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
    </AuthProvider>
  </React.StrictMode>
);
