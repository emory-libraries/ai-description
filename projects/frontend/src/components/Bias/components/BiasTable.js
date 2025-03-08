/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React from 'react';
import {
  Table,
  Header,
  Box,
  StatusIndicator
} from "@cloudscape-design/components";
import { getBiasLevelColor } from '../utils/biasHelpers';

/**
 * Table component that displays bias entries
 */
export const BiasTable = ({ biasData, onBiasSelect }) => {
  return (
    <Table
      header={<Header variant="h3">Identified Biases</Header>}
      columnDefinitions={[
        {
          id: "page",
          header: "Page",
          cell: item => item.pageNumber || "N/A",
          sortingField: "pageNumber"
        },
        {
          id: "type",
          header: "Bias Type",
          cell: item => item.type || item.bias_type,
          sortingField: "type"
        },
        {
          id: "level",
          header: "Risk Level",
          cell: item => (
            <StatusIndicator type={getBiasLevelColor(item.level || item.bias_level)}>
              {item.level || item.bias_level}
            </StatusIndicator>
          )
        },
        {
          id: "explanation",
          header: "Explanation",
          cell: item => (
            <div style={{
              maxWidth: "400px",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis"
            }}>
              {item.explanation}
            </div>
          )
        }
      ]}
      items={biasData || []}
      selectionType="single"
      onSelectionChange={({ detail }) => {
        if (detail.selectedItems.length > 0) {
          onBiasSelect(detail.selectedItems[0]);
        }
      }}
      empty={
        <Box textAlign="center" color="text-body-secondary">
          <b>No biases found</b>
          <Box padding={{ bottom: "s" }}>
            No biases were detected in this document
          </Box>
        </Box>
      }
    />
  );
};
