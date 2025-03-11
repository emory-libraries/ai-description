/*
 * Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
 * Terms and the SOW between the parties dated 2025.
 */

// components/Bias/components/BiasTable.js

import React, { useState } from 'react';
import {
  Table,
  Box,
  StatusIndicator,
  SpaceBetween,
  Button,
} from '@cloudscape-design/components';
import { getBiasLevelColor } from '../utils/biasHelpers';

/**
 * Table component that displays bias entries
 */
export const BiasTable = ({ biasData, onBiasSelect }) => {
  // State to track which filters are active
  const [filters, setFilters] = useState({
    low: false,
    medium: false,
    high: false
  });

  // Normalize bias level values for consistent filtering
  const normalizeLevel = (level) => {
    level = String(level).toLowerCase();
    return level;
  };

  // Filter the bias data based on active filters
  const filteredData = biasData?.filter(item => {
    // If no filters are active, show all items
    if (!filters.low && !filters.medium && !filters.high) {
      return true;
    }

    const level = normalizeLevel(item.level || item.bias_level);

    return (
      (filters.low && level === 'low') ||
      (filters.medium && level === 'medium') ||
      (filters.high && level === 'high')
    );
  });

  // Toggle filter handler
  const toggleFilter = (level) => {
    setFilters(prevFilters => ({
      ...prevFilters,
      [level]: !prevFilters[level]
    }));
  };

  return (
    <SpaceBetween size="m">

      <SpaceBetween direction="horizontal" size="xs" alignItems="center">
        <Box>Filter by risk level:</Box>

        <Button
          variant={filters.low ? "primary" : "normal"}
          onClick={() => toggleFilter('low')}
        >
          <StatusIndicator type={getBiasLevelColor('low')}>
            Low
          </StatusIndicator>
        </Button>

        <Button
          variant={filters.medium ? "primary" : "normal"}
          onClick={() => toggleFilter('medium')}
        >
          <StatusIndicator type={getBiasLevelColor('medium')}>
            Medium
          </StatusIndicator>
        </Button>

        <Button
          variant={filters.high ? "primary" : "normal"}
          onClick={() => toggleFilter('high')}
        >
          <StatusIndicator type={getBiasLevelColor('high')}>
            High
          </StatusIndicator>
        </Button>

        {(filters.low || filters.medium || filters.high) && (
          <Button
            variant="link"
            onClick={() => setFilters({ low: false, medium: false, high: false })}
          >
            Clear filters
          </Button>
        )}
      </SpaceBetween>

      <Table
        columnDefinitions={[
          {
            id: 'page',
            header: 'Page',
            cell: (item) => item.pageNumber || 'N/A',
            sortingField: 'pageNumber',
          },
          {
            id: 'type',
            header: 'Bias Type',
            cell: (item) => item.type || item.bias_type,
            sortingField: 'type',
          },
          {
            id: 'level',
            header: 'Risk Level',
            cell: (item) => (
              <StatusIndicator type={getBiasLevelColor(item.level || item.bias_level)}>
                {item.level || item.bias_level}
              </StatusIndicator>
            ),
          },
          {
            id: 'explanation',
            header: 'Explanation',
            cell: (item) => (
              <div
                style={{
                  maxWidth: '400px',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {item.explanation}
              </div>
            ),
          },
        ]}
        items={filteredData || []}
        selectionType="single"
        onSelectionChange={({ detail }) => {
          if (detail.selectedItems.length > 0) {
            onBiasSelect(detail.selectedItems[0]);
          }
        }}
        empty={
          <Box textAlign="center" color="text-body-secondary">
            <b>No biases found</b>
            <Box padding={{ bottom: 's' }}>
              {filters.low || filters.medium || filters.high ?
                'No biases match the selected filters' :
                'No biases were detected in this document'}
            </Box>
          </Box>
        }
      />
    </SpaceBetween>
  );
};
