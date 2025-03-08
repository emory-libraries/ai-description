/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { buildApiUrl } from './utils/apiUrls';


const Login = () => {
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
  
    try {
      // Validate the API key by making a test request to a protected endpoint
      const url = buildApiUrl('/api/overall_progress');
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'x-api-key': apiKey
        },
      });
  
      if (!response.ok) {
        throw new Error('Invalid API key');
      }
  
      // If the API key is valid, store it
      console.log("Login successful, storing token");
      login(apiKey);
      console.log("About to navigate to home");
      // Add a short delay before navigation to ensure state is updated
      setTimeout(() => {
        navigate('/', { replace: true });
      }, 100);
      console.log("Navigation command issued");
  
    } catch (error) {
      setError(error.message || 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error}</div>}
      <input
        type="password"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        placeholder="Enter your API key"
        disabled={isLoading}
      />
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
};

export default Login;
