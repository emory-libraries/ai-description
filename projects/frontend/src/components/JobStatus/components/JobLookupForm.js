/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import {
  Container,
  Header,
  Button,
  Form,
  FormField,
  Input
} from "@cloudscape-design/components";

const JobLookupForm = ({ jobName, setJobName, handleSubmitJobName }) => {
  const handleFormSubmit = (e) => {
    e.preventDefault(); // Prevent default form submission
    handleSubmitJobName(e);
  };

  return (
    <Container
      header={
        <Header variant="h2" description="Enter a job name to retrieve status information">
          Job results search
        </Header>
      }
    >
      <form onSubmit={handleFormSubmit}>
        <Form
          actions={
            <Button
              variant="primary"
              formAction="submit"
              type="submit"
              disabled={!jobName.trim()}
            >
              Submit
            </Button>
          }
        >
          <FormField>
            <Input
              value={jobName}
              onChange={({ detail }) => setJobName(detail.value)}
              placeholder="e.g. job-001"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && jobName.trim()) {
                  e.preventDefault();
                  handleSubmitJobName(e);
                }
              }}
            />
          </FormField>
        </Form>
      </form>
    </Container>
  );
};

export default JobLookupForm;
