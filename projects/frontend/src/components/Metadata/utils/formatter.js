/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
export function formatValue(val) {
    // Debug logging to see what's happening (remove in production)
    console.log('Formatting value:', val, 'Type:', typeof val, 'Is Array:', Array.isArray(val));

    if (val === null || val === undefined) {
      return '';
    }

    if (Array.isArray(val) && val.length === 0) {
      return '';
    }

    // Handle page_biases specifically
    if (val && typeof val === 'object' && 'page_biases' in val) {
      try {
        return JSON.stringify(val.page_biases, null, 2);
      } catch (e) {
        return 'Error formatting page biases data';
      }
    }

    // Handle the case where fieldKey is 'page_biases' but the structure is unexpected
    if (val && typeof val === 'object' && !Array.isArray(val) &&
        Object.keys(val).some(key => key.includes('bias'))) {
      try {
        return JSON.stringify(val, null, 2);
      } catch (e) {
        return 'Complex bias data structure';
      }
    }

    if (Array.isArray(val) && val.length > 0 &&
        typeof val[0] === 'object' && val[0] !== null &&
        'biases' in val[0]) {
      return val.map((page, pageIndex) => {
        return `Page ${pageIndex + 1}:\n` + page.biases.map(bias =>
          `Type: ${bias.type}\nLevel: ${bias.level}\nExplanation: ${bias.explanation}`
        ).join('\n\n');
      }).join('\n\n');
    }

    if (typeof val === 'object' && val !== null && 'transcriptions' in val) {
      const result = [];
      val.transcriptions.forEach((trans, index) => {
        result.push(`Page ${index + 1}:`);
        if (trans.printed_text && trans.printed_text.length > 0) {
          result.push('Printed text:');
          trans.printed_text.forEach(text => {
            result.push(`  ${text}`);
          });
        }
        if (trans.handwriting && trans.handwriting.length > 0) {
          result.push('Handwriting:');
          trans.handwriting.forEach(text => {
            result.push(`  ${text}`);
          });
        }
        result.push('');
      });

      if (val.model_notes) {
        result.push('Notes:');
        result.push(`${val.model_notes}`);
      }

      return result.join('\n');
    }

    if (typeof val === 'object' && val !== null && 'biases' in val) {
      if (Array.isArray(val.biases) && val.biases.length === 0) {
        return 'No biases found';
      }
      return val.biases.map(bias => `${bias}`).join(', ') || 'No biases found';
    }

    if (Array.isArray(val)) {
      if (typeof val[0] === 'string') {
        return val.map(item => String(item).trim()).join(', ');
      }
      return JSON.stringify(val);
    }

    if (typeof val === 'object' && val !== null && 'value' in val) {
      if (Array.isArray(val.value)) {
        return val.value.map(item => String(item).trim()).join(', ');
      }
      return String(val.value);
    }

    if (typeof val === 'object' && val !== null) {
      return JSON.stringify(val, null, 2);
    }

    return String(val || '');
}
