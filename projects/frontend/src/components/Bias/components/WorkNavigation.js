/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// components/Bias/components/WorkNavigation.js

import React from 'react';
import {
  Container,
  Header,
  Box,
  Spinner,
  StatusIndicator,
  SideNavigation,
  SpaceBetween,
} from '@cloudscape-design/components';

export const WorkNavigation = React.memo(function WorkNavigation({ allWorks, selectedWork, isLoading, onWorkSelect }) {
  // Function to get StatusIndicator props based on work status
  const getStatusIndicatorProps = (status) => {
    switch (status) {
      case 'REVIEWED':
        return { type: 'success', children: 'Reviewed' };
      case 'READY FOR REVIEW':
        return { type: 'info', children: 'Ready' };
      case 'FAILED TO PROCESS':
        return { type: 'error', children: 'Failed' };
      default:
        return { type: 'in-progress', children: 'Pending' };
    }
  };

  // Create navigation items for SideNavigation
  const workNavigationItems = React.useMemo(
    () =>
      allWorks.map((work) => ({
        type: 'link',
        text: work.work_id,
        href: `#${work.work_id}`,
        info: <StatusIndicator {...getStatusIndicatorProps(work.work_status)} />,
        key: work.work_id,
      })),
    [allWorks],
  );
  const selectedHref = selectedWork ? `#${selectedWork.work_id}` : '';

  return (
    <Container header={<Header variant="h2">Works</Header>}>
      {isLoading && allWorks.length === 0 ? (
        <Box textAlign="center" padding="l">
          <SpaceBetween size="s" direction="vertical" alignItems="center">
            <Spinner />
            <Box variant="p">Loading works...</Box>
          </SpaceBetween>
        </Box>
      ) : allWorks.length === 0 ? (
        <Box textAlign="center" padding="l">
          <Box variant="p">No works found</Box>
        </Box>
      ) : (
        <SideNavigation
          activeHref={selectedHref}
          items={workNavigationItems}
          header={{
            text: `${allWorks.length} work${allWorks.length !== 1 ? 's' : ''}`,
            href: '#',
          }}
          onFollow={({ detail }) => {
            if (!detail.external) {
              const workId = detail.href.substring(1);
              const workToSelect = allWorks.find((work) => work.work_id === workId);

              if (workToSelect) {
                onWorkSelect(workToSelect);
              }
            }
          }}
        />
      )}
    </Container>
  );
});
