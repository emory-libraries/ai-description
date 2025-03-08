/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React from 'react';
import {
  Cards,
  Badge,
  Box
} from "@cloudscape-design/components";

const WorkItemsCards = ({ works }) => {
  return (
    <Cards
      cardDefinition={{
        header: item => item.work_id,
        sections: [
          {
            id: "status",
            header: "Status",
            content: item => {
              let statusType = "info";
              if (item.work_status === "READY FOR REVIEW") statusType = "success";
              if (item.work_status === "FAILED TO PROCESS") statusType = "error";

              return <Badge color={statusType}>{item.work_status}</Badge>;
            }
          }
        ]
      }}
      cardsPerRow={[
        { cards: 1 },
        { minWidth: 500, cards: 2 }
      ]}
      items={works}
      loadingText="Loading work items"
      empty={
        <Box textAlign="center" color="text-body-secondary">
          <b>No work items found</b>
          <Box padding={{ bottom: "s" }}>
            This job has no associated work items
          </Box>
        </Box>
      }
    />
  );
};

export default WorkItemsCards;
