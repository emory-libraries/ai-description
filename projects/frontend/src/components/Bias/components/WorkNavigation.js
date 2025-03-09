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
  StatusIndicator,
} from '@cloudscape-design/components';

/**
 * Navigation component for work selection
 */
export const WorkNavigation = ({ allWorks, selectedWork, isLoading, onWorkSelect }) => {
  const getStatusType = (status) => {
    if (status === 'READY FOR REVIEW') return 'success';
    if (status === 'FAILED TO PROCESS') return 'error';
    return 'in-progress';
  };

  const workNavigationItems = allWorks.map((work) => ({
    type: 'link',
    text: `${work.work_id}`,
    href: `#${work.work_id}`,
    info: <StatusIndicator type={getStatusType(work.work_status)} />,
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
            href: '#',
          }}
          onFollow={({ detail }) => {
            if (!detail.external) {
              const workId = detail.href.substring(1);
              const selectedWork = allWorks.find((work) => work.work_id === workId);
              if (selectedWork) {
                onWorkSelect(selectedWork);
              }
            }
          }}
        />
      )}
    </Container>
  );
};
