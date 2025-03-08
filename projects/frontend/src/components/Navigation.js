/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import { SideNavigation } from "@cloudscape-design/components";
import { buildFrontendPath } from '../utils/frontendPaths';

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
              text: "Job results search",
              href: buildFrontendPath("/")
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
