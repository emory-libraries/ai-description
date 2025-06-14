/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppLayout,
  ContentLayout,
  SpaceBetween,
  Header,
  Button,
  Alert,
  Grid,
  BreadcrumbGroup,
  Box,
} from '@cloudscape-design/components';
import { AWSSideNavigation } from '../Navigation';
import { MetadataProvider, useMetadataContext } from './MetadataContext';
import WorkNavigation from './components/WorkNavigation';
import DocumentPreview from './components/DocumentPreview';
import MetadataEditor from './components/MetadataEditor';
import { buildFrontendPath } from '../../utils/frontendPaths';

function MetadataContent() {
  const navigate = useNavigate();
  const { jobName, error, isLoading, allWorks, selectedWork, downloadAllMetadata } = useMetadataContext();

  const breadcrumbItems = [
    { text: 'Job results search', href: buildFrontendPath('/') },
    { text: `Metadata Analysis: ${jobName || ''}` },
  ];

  // Check work status
  const isWorkReadyForReview =
    selectedWork && (selectedWork.work_status === 'READY FOR REVIEW' || selectedWork.work_status === 'REVIEWED');
  const isWorkFailed = selectedWork && selectedWork.work_status === 'FAILED TO PROCESS';

  // Determine what to render in the main content area
  const renderContent = () => {
    if (!selectedWork) {
      return (
        <Box padding="l" textAlign="center">
          <h2>Select a work from the list to view details</h2>
        </Box>
      );
    } else if (isWorkFailed) {
      return (
        <Box padding="l" textAlign="center">
          <h2>Work Status: {selectedWork.work_status}</h2>
          <p>This document could not be processed successfully.</p>
        </Box>
      );
    } else if (!isWorkReadyForReview) {
      return (
        <Box padding="l" textAlign="center">
          <h2>Work Status: {selectedWork.work_status}</h2>
          <p>This work is not ready for review yet. Please wait for processing to complete.</p>
        </Box>
      );
    } else {
      return (
        <>
          <DocumentPreview />
          <MetadataEditor />
        </>
      );
    }
  };

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/metadata" />}
      toolsHide={true}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      navigationHide={true}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="View and edit document metadata"
              actions={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button onClick={() => navigate('/')} variant="link">
                    Back to job status
                  </Button>
                  <Button
                    variant="primary"
                    onClick={downloadAllMetadata}
                    loading={isLoading}
                    disabled={!allWorks || allWorks.length === 0}
                  >
                    Download All Metadata
                  </Button>
                </SpaceBetween>
              }
            >
              Metadata Results: {jobName}
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" header="Error">
                {error}
              </Alert>
            )}

            <Grid gridDefinition={[{ colspan: 3 }, { colspan: 9 }]}>
              <WorkNavigation />
              <SpaceBetween size="l">{renderContent()}</SpaceBetween>
            </Grid>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

function Metadata() {
  return (
    <MetadataProvider>
      <MetadataContent />
    </MetadataProvider>
  );
}

export default Metadata;
