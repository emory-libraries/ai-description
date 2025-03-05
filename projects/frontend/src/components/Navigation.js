/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import { SideNavigation } from "@cloudscape-design/components";

export function AWSSideNavigation({ activeHref }) {
  return (
    <SideNavigation
      activeHref={activeHref}
      header={{
        text: "Document Analysis Service"
      }}
      items={[
        {
          type: "section",
          text: "Jobs",
          items: [
            {
              type: "link",
              text: "Job Status",
              href: "/"
            }
          ]
        },
        {
          type: "section",
          text: "Analysis Types",
          items: [
            {
              type: "link",
              text: "Metadata Analysis",
              href: "/metadata"
            },
            {
              type: "link",
              text: "Bias Analysis",
              href: "/bias"
            }
          ]
        },
        {
          type: "divider"
        }
      ]}
    />
  );
}
