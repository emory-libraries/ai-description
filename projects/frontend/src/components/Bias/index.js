/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// components/Bias/index.js

import React from 'react';
import {
  AppLayout,
  Container,
  ContentLayout,
  SpaceBetween,
  Header,
  Box,
  Button,
  Alert,
  Grid,
  Spinner,
  BreadcrumbGroup,
} from '@cloudscape-design/components';
import { AWSSideNavigation } from '../Navigation';
import { WorkNavigation } from './components/WorkNavigation';
import { BiasTable } from './components/BiasTable';
import { BiasDetails } from './components/BiasDetails';
import { BiasProvider, useBiasContext } from './BiasContext';
import { buildFrontendPath } from '../../utils/frontendPaths';

function BiasContent() {
  const {
    jobName,
    biasData,
    imageData,
    selectedBias,
    handleBiasSelect,
    handleBackToBiasList,
    allWorks,
    selectedWork,
    handleWorkSelect,
    error,
    isLoading,
    navigateToJobs,
    updateReviewStatus,
  } = useBiasContext();

  const breadcrumbItems = [
    { text: 'Job results search', href: buildFrontendPath('/') },
    { text: `Bias Analysis: ${jobName || ''}` },
  ];

  // Check if the current work is reviewed
  const isReviewed = selectedWork?.work_status === 'REVIEWED';

  return (
    <AppLayout
      toolsHide={true}
      navigation={<AWSSideNavigation activeHref="/bias" />}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      navigationHide={true}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description={`Bias analysis results for the specified document set`}
              actions={
                <Button variant="link" onClick={navigateToJobs}>
                  Back to Job Status
                </Button>
              }
            >
              Bias Analysis: {jobName}
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
              {/* Left panel - Navigation */}
              <WorkNavigation
                allWorks={allWorks}
                selectedWork={selectedWork}
                isLoading={isLoading}
                onWorkSelect={handleWorkSelect}
              />

              {/* Right panel - Bias details */}
              <Container
                header={
                  <Header
                    variant="h2"
                    actions={
                      <SpaceBetween direction="horizontal" size="xs">
                        {selectedBias ? (
                          <Button onClick={handleBackToBiasList} variant="normal">
                            Back to bias list
                          </Button>
                        ) : null}
                        {selectedWork && (
                          <>
                            {isReviewed ? (
                              <Button onClick={() => updateReviewStatus(selectedWork, 'READY FOR REVIEW')}>
                                Rescind reviewed status
                              </Button>
                            ) : (
                              <Button onClick={() => updateReviewStatus(selectedWork, 'REVIEWED')}>
                                Mark as reviewed
                              </Button>
                            )}
                          </>
                        )}
                      </SpaceBetween>
                    }
                  >
                    Bias Analysis Results
                  </Header>
                }
              >
                {isLoading && selectedWork ? (
                  <Box textAlign="center" padding="l">
                    <SpaceBetween size="s" direction="vertical" alignItems="center">
                      <Spinner />
                      <Box variant="p">Loading bias details...</Box>
                    </SpaceBetween>
                  </Box>
                ) : selectedWork ? (
                  <SpaceBetween size="l">
                    {selectedWork.work_status === 'FAILED TO PROCESS' ? (
                      <Box textAlign="center" padding="l">
                        <Alert type="error" header="Work processing failed">
                          This work failed to process. No bias analysis data is available.
                        </Alert>
                      </Box>
                    ) : selectedBias ? (
                      <BiasDetails bias={selectedBias} imageUrl={imageData[selectedBias.imageUri]} />
                    ) : (
                      <>
                        <BiasTable biasData={biasData} onBiasSelect={handleBiasSelect} />
                      </>
                    )}
                  </SpaceBetween>
                ) : (
                  <Box textAlign="center" padding="l">
                    <Box variant="h3">Select a work</Box>
                    <Box variant="p">Please select a work from the list to view bias analysis results.</Box>
                  </Box>
                )}
              </Container>
            </Grid>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

function Bias() {
  return (
    <BiasProvider>
      <BiasContent />
    </BiasProvider>
  );
}

export default Bias;
