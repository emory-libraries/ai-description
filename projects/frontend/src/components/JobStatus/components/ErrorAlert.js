/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import { Alert } from "@cloudscape-design/components";

const ErrorAlert = ({ message }) => {
  return (
    <Alert type="error" header="Error">
      {message}
    </Alert>
  );
};

export default ErrorAlert;
