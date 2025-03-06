/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

/**
 * Returns the appropriate color for a bias level
 * @param {string} level - The bias level (high, medium, low)
 * @returns {string} The corresponding status indicator color
 */
export const getBiasLevelColor = (level) => {
    if (!level) return "grey";
  
    switch (level.toLowerCase()) {
      case 'high': return "error";
      case 'medium': return "warning";
      case 'low': return "success";
      default: return "grey";
    }
  };
  