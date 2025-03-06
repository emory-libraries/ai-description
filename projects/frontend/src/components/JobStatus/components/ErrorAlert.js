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
