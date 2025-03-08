/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Container,
  Header,
  Box,
  Spinner,
  SideNavigation,
  SpaceBetween,
  StatusIndicator
} from "@cloudscape-design/components";
import { useMetadataContext } from '../MetadataContext';

function WorkNavigation() {
  const {
    allWorks,
    selectedWork,
    isLoading,
    handleWorkSelect
  } = useMetadataContext();

  const workNavigationItems = allWorks.map(work => ({
    type: 'link',
    text: `Work ID: ${work.work_id}`,
    href: `#${work.work_id}`,
    info: <StatusIndicator
      type={work.work_status === 'READY FOR REVIEW' ? 'success' : 'in-progress'}
    />,
  }));

  return (
    <Container header={<Header variant="h2">Works</Header>}>
      {isLoading && !selectedWork ? (
        <Box textAlign="center" padding="l">
          <SpaceBetween size="s" direction="vertical" alignItems="center">
            <Spinner />
            <Box variant="p">Loading works...</Box>
          </SpaceBetween>
        </Box>
      ) : (
        <SideNavigation
          activeHref={selectedWork ? `#${selectedWork.work_id}` : undefined}
          items={workNavigationItems}
          header={{
            text: `${allWorks.length} work${allWorks.length !== 1 ? 's' : ''}`,
            href: '#'
          }}
          onFollow={({ detail }) => {
            if (!detail.external) {
              // Extract the work_id from the href
              const workId = detail.href.substring(1);

              // Find the work with this ID
              const workToSelect = allWorks.find(work => work.work_id === workId);

              // If found, select this work
              if (workToSelect) {
                handleWorkSelect(workToSelect);
              }
            }
          }}
        />
      )}
    </Container>
  );
}

export default WorkNavigation;
