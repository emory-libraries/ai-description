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
  return (
    <Container
      header={
        <Header variant="h2" description="Enter a job name to retrieve status information">
          Job Lookup
        </Header>
      }
    >
      <Form
        actions={
          <Button
            variant="primary"
            formAction="submit"
            onClick={handleSubmitJobName}
            disabled={!jobName.trim()}
          >
            Submit
          </Button>
        }
      >
        <FormField
          label="Job name"
          description="Enter the job identifier to view processing status"
        >
          <Input
            value={jobName}
            onChange={({ detail }) => setJobName(detail.value)}
            placeholder="Enter job name"
          />
        </FormField>
      </Form>
    </Container>
  );
};

export default JobLookupForm;