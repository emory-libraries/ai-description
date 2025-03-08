/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  AppLayout,
  ContentLayout,
  SpaceBetween,
  Header,
  Button,
  Alert,
  Grid,
  BreadcrumbGroup
} from "@cloudscape-design/components";
import { AWSSideNavigation } from '../Navigation';
import { MetadataProvider, useMetadataContext } from './MetadataContext';
import WorkNavigation from './components/WorkNavigation';
import DocumentPreview from './components/DocumentPreview';
import MetadataEditor from './components/MetadataEditor';
import { buildFrontendPath } from '../../utils/frontendPaths';

function MetadataContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    jobName,
    error,
    isLoading,
    allWorks,
    selectedWork,
    metadata,
    downloadAllMetadata
  } = useMetadataContext();

  const breadcrumbItems = [
    { text: 'Document Analysis Service', href: buildFrontendPath('/') },
    { text: 'Job Status', href: buildFrontendPath('/') },
    { text: `Metadata Analysis: ${jobName || ''}` }
  ];

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/metadata" />}
      toolsHide={true}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      defaultHideNavigation={true}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="View and edit document metadata"
              actions={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button
                    onClick={() => navigate('/')}
                    variant="link"
                  >
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
              <SpaceBetween size="l">
                {selectedWork && metadata ? (
                  <>
                    <DocumentPreview />
                    <MetadataEditor />
                  </>
                ) : null}
              </SpaceBetween>
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
