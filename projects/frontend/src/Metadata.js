/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { useAuth } from './AuthContext'; // Use your custom auth context
import {
  AppLayout,
  Container,
  ContentLayout,
  SpaceBetween,
  Header,
  Box,
  Button,
  Alert,
  Spinner,
  SideNavigation,
  Grid,
  Textarea,
  FormField,
  StatusIndicator,
  BreadcrumbGroup
} from "@cloudscape-design/components";
import { AWSSideNavigation } from './components/Navigation';

function Metadata() {
  const { token, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { jobName } = location.state || {};
  const [selectedWork, setSelectedWork] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState({});
  const [modifiedFields, setModifiedFields] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [allWorks, setAllWorks] = useState([]);

  const initializeS3Client = useCallback(() => {
    return new S3Client({
      region: "us-east-1",
      credentials: {
        accessKeyId: process.env.REACT_APP_S3_ACCESS_KEY_ID,
        secretAccessKey: process.env.REACT_APP_S3_SECRET_ACCESS_KEY,
        sessionToken: process.env.REACT_APP_S3_SESSION_TOKEN,
      }
    });
  }, []);

  const fetchImage = useCallback(async (uri) => {
    if (!uri || typeof uri !== 'string') {
      console.error('Invalid URI provided:', uri);
      return null;
    }

    try {
      const s3Client = initializeS3Client();
      const matches = uri.match(/s3:\/\/([^/]+)\/(.+)/);

      if (!matches) {
        console.error('Invalid S3 URI format:', uri);
        return null;
      }

      const [, bucket, key] = matches;
      const command = new GetObjectCommand({ Bucket: bucket, Key: key });
      const response = await s3Client.send(command);
      const arrayBuffer = await response.Body.transformToByteArray();
      const blob = new Blob([arrayBuffer]);
      const imageUrl = URL.createObjectURL(blob);
      return imageUrl;
    } catch (err) {
      console.error('Error fetching image:', err);
      return null;
    }
  }, [initializeS3Client]);

  const fetchWorkDetails = useCallback(async (workId, jobName) => {
    if (!token) return;
    
    try {
      const response = await fetch(
        `/api/results?job_name=${jobName}&work_id=${workId}`,
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`Failed to fetch work details: ${response.status}`);
      }

      const data = await response.json();
      return data.item;
    } catch (err) {
      console.error('Error fetching work details:', err);
      throw err;
    }
  }, [token, logout, navigate]);

  const handleWorkSelect = useCallback(async (work) => {
    setIsLoading(true);
    setSelectedWork(work);
    setMetadata(null);
    setImageData({});
    setError(null);
    setModifiedFields({});

    try {
      const workDetails = await fetchWorkDetails(work.work_id, work.job_name);
      setMetadata(workDetails);

      if (workDetails.image_s3_uris && workDetails.image_s3_uris.length > 0) {
        const imagePromises = workDetails.image_s3_uris.map(async uri => {
          const imageUrl = await fetchImage(uri);
          return { uri, imageUrl };
        });
        const images = await Promise.all(imagePromises);
        const newImageData = {};
        images.forEach(({ uri, imageUrl }) => {
          if (imageUrl) newImageData[uri] = imageUrl;
        });
        setImageData(newImageData);
      }
    } catch (err) {
      console.error('Error in handleWorkSelect:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [fetchWorkDetails, fetchImage]);

  const handleMetadataEdit = (key, value) => {
    if (key === 'job_name' || key === 'work_id') return;
    let processedValue = value;
    if (typeof value === 'object' && value !== null && 'value' in value) {
      processedValue = {
        ...value
      };
    }
    setMetadata(prev => ({
      ...prev,
      [key]: processedValue
    }));
    setModifiedFields(prev => ({
      ...prev,
      [key]: processedValue
    }));
  };

  const updateMetadata = async () => {
    if (!token || !selectedWork) {
      setError('Unable to update: Missing required data');
      return;
    }
    try {
      setIsLoading(true);
      const processedModifiedFields = {};
      Object.entries(modifiedFields).forEach(([key, value]) => {
        if (typeof value === 'object' && value !== null && 'value' in value) {
          if (typeof value.value === 'string') {
            processedModifiedFields[key] = {
              ...value,
              value: value.value.includes(',') ?
                value.value.split(',').map(item => item.trim()) :
                value.value
            };
          } else {
            processedModifiedFields[key] = value;
          }
        } else if (typeof value === 'string' &&
                  metadata[key] &&
                  typeof metadata[key] === 'object' &&
                  Array.isArray(metadata[key].value)) {
          processedModifiedFields[key] = {
            ...metadata[key],
            value: value.includes(',') ?
              value.split(',').map(item => item.trim()) :
              [value]
          };
        } else {
          processedModifiedFields[key] = value;
        }
      });

      console.log("Sending update with fields:", processedModifiedFields);

      const url = `/api/results`;
      const requestBody = {
        job_name: selectedWork.job_name,
        work_id: selectedWork.work_id,
        updated_fields: processedModifiedFields
      };

      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        // Handle authentication errors
        if (response.status === 401 || response.status === 403) {
          logout();
          navigate('/login');
          throw new Error('Authentication failed. Please log in again.');
        }
        
        const errorText = await response.text();
        console.error('API Error Response:', errorText);
        throw new Error(`Failed to update metadata: ${response.status}`);
      }

      const data = await response.json();
      setMetadata(data.item);
      setModifiedFields({});
      setError(null);
    } catch (err) {
      console.error('Error updating metadata:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const fetchAllWorks = async () => {
      if (!token || !jobName) return;

      try {
        setIsLoading(true);

        const response = await fetch(
          `/api/job_progress?job_name=${jobName}`,
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}` // Use your custom auth token
            }
          }
        );

        if (!response.ok) {
          // Handle authentication errors
          if (response.status === 401 || response.status === 403) {
            logout();
            navigate('/login');
            throw new Error('Authentication failed. Please log in again.');
          }
          throw new Error(`Failed to fetch job data: ${response.status}`);
        }

        const jobData = await response.json();
        const works = [];

        if (jobData.job_progress) {
          Object.entries(jobData.job_progress).forEach(([status, ids]) => {
            ids.forEach(id => {
              works.push({
                work_id: id,
                work_status: status,
                job_name: jobName,
                job_type: jobData.job_type
              });
            });
          });
        }

        setAllWorks(works);

        if (location.state?.workId) {
          const workToSelect = works.find(w => w.work_id === location.state.workId);
          if (workToSelect) {
            await handleWorkSelect(workToSelect);
          } else if (works.length > 0) {
            await handleWorkSelect(works[0]);
          }
        } else if (works.length > 0) {
          await handleWorkSelect(works[0]);
        }
      } catch (err) {
        console.error('Error fetching all works:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (token && jobName) {
      fetchAllWorks();
    }
  }, [token, jobName, handleWorkSelect, location.state, logout, navigate]);

  const downloadAllMetadata = async () => {
    if (!allWorks || allWorks.length === 0 || !token) {
      console.error('No works available or not authenticated to download metadata.');
      return;
    }

    try {
      setIsLoading(true);
      const allMetadataResults = [];
      const currentJobName = selectedWork?.job_name || jobName;
      if (!currentJobName) {
        throw new Error('Job name is undefined. Please select a work first.');
      }
      for (let i = 0; i < allWorks.length; i++) {
        const work = allWorks[i];
        try {
          const metadata = await fetchWorkDetails(work.work_id, work.job_name);
          allMetadataResults.push({
            ...metadata,
            work_id: work.work_id,
            work_status: work.work_status
          });
        } catch (err) {
          console.error(`Error fetching work ${work.work_id}:`, err);
          allMetadataResults.push({
            work_id: work.work_id,
            work_status: 'ERROR',
            error: 'Failed to fetch metadata'
          });
        }
      }

      const headers = ['work_id', 'work_status'];
      const metadataKeys = new Set();
      allMetadataResults.forEach(metadata => {
        Object.keys(metadata).forEach(key => {
          if (!['work_id', 'work_status', 'image_s3_uris'].includes(key)) {
            metadataKeys.add(key);
          }
        });
      });
      headers.push(...Array.from(metadataKeys));

      const rows = allMetadataResults.map(metadata => {
        return headers.map(header => {
          const value = metadata[header];
          if (!value) return '""';
          if (typeof value === 'object' && value !== null) {
            if ('explanation' in value && 'value' in value) {
              return `"${formatValue(value.value)} (${value.explanation.replace(/"/g, '""')})"`;
            }
            return `"${formatValue(value).replace(/"/g, '""')}"`;
          }
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',');
      });

      const csvContent = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${currentJobName}-all-results-${new Date().toISOString()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
      setError(null);
    } catch (error) {
      console.error('Error downloading all metadata:', error);
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatValue = (val) => {
    if (val === null || val === undefined) {
      return '';
    }

    if (Array.isArray(val) && val.length === 0) {
      return '';
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
  };

  const workNavigationItems = allWorks.map(work => ({
    type: 'link',
    text: `Work ID: ${work.work_id}`,
    href: `#${work.work_id}`,
    info: <StatusIndicator type={work.work_status === 'READY FOR REVIEW' ? 'success' : 'in-progress'} />,
  }));

  const breadcrumbItems = [
    { text: 'Document Analysis Service', href: '/' },
    { text: 'Job Status', href: '/' },
    { text: `Metadata Analysis: ${jobName || ''}` }
  ];

  const renderMetadataSection = (key, value) => {
    if (key === 'image_s3_uris' || key === 'work_id' ||
        key === 'job_name' || key === 'work_status') {
      return null;
    }

    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    if (Array.isArray(value) && value.length === 0) {
      return (
        <Container
          key={key}
          header={<Header variant="h3">{formattedKey}</Header>}
        >
          <FormField
            label="Value"
            description="Enter comma-separated values for this field. Currently empty."
          >
            <Textarea
              value=""
              onChange={({ detail }) => handleMetadataEdit(key,
                detail.value.split(',').filter(item => item.trim().length > 0)
              )}
              rows={2}
              placeholder="Enter comma-separated values..."
            />
          </FormField>
        </Container>
      );
    }

    const isNestedStructure = value &&
      typeof value === 'object' &&
      ('explanation' in value || 'value' in value);

    if (isNestedStructure) {
      return (
        <Container
          key={key}
          header={<Header variant="h3">{formattedKey}</Header>}
        >
          <SpaceBetween size="m">
            <FormField label="Explanation">
              <Textarea
                value={value.explanation || ''}
                onChange={({ detail }) => handleMetadataEdit(key, {
                  ...value,
                  explanation: detail.value
                })}
                rows={3}
              />
            </FormField>

            <FormField
              label="Value"
              description={Array.isArray(value.value) ?
                "Enter values separated by commas" :
                "Enter value for this field"}
            >
              <Textarea
                value={value.value ? formatValue(value.value) : ''}
                onChange={({ detail }) => handleMetadataEdit(key, {
                  ...value,
                  value: detail.value
                })}
                rows={3}
                placeholder={Array.isArray(value.value) ?
                  "e.g. value1, value2, value3" :
                  "Enter value here..."}
              />
            </FormField>
          </SpaceBetween>
        </Container>
      );
    }

    if (Array.isArray(value)) {
      return (
        <Container
          key={key}
          header={<Header variant="h3">{formattedKey}</Header>}
        >
          <FormField
            label="Value"
            description="Enter values separated by commas"
          >
            <Textarea
              value={formatValue(value)}
              onChange={({ detail }) => handleMetadataEdit(key,
                detail.value.split(',').map(item => item.trim()).filter(item => item)
              )}
              rows={4}
              placeholder="e.g. value1, value2, value3"
            />
          </FormField>
        </Container>
      );
    }

    return (
      <Container
        key={key}
        header={<Header variant="h3">{formattedKey}</Header>}
      >
        <FormField
          label="Value"
          description={
            typeof value === 'object' ?
              "JSON object - Edit carefully" :
              `Enter ${typeof value} value`
          }
        >
          <Textarea
            value={formatValue(value)}
            onChange={({ detail }) => handleMetadataEdit(key, detail.value)}
            rows={4}
            placeholder={`Enter ${formattedKey.toLowerCase()} here...`}
          />
        </FormField>
      </Container>
    );
  };

  return (
    <AppLayout
      navigation={<AWSSideNavigation activeHref="/metadata" />}
      toolsHide = {true}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1"
              description="View and edit document metadata"
              actions={
                <SpaceBetween direction="horizontal" size="xs">
                  <Button
                    onClick={() => navigate('/')}
                    variant="link"
                  >
                    Back to job status
                  </Button>
                  <Button
                    variant="primary"
                    onClick={downloadAllMetadata}
                    loading={isLoading}
                    disabled={!allWorks || allWorks.length === 0}
                  >
                    Download All Metadata
                  </Button>
                </SpaceBetween>
              }
            >
              Metadata Results: {jobName}
            </Header>
          }
        >
          <SpaceBetween size="l">
            {error && (
              <Alert type="error" header="Error">
                {error}
              </Alert>
            )}

            <Grid gridDefinition={[{ colspan: 3 }, { colspan: 9 }]}>
              {/* Left panel - Work selection */}
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
                        console.log("Selected work ID from navigation:", workId);

                        // Find the work with this ID
                        const workToSelect = allWorks.find(work => work.work_id === workId);

                        // If found, select this work
                        if (workToSelect) {
                          console.log("Found work to select:", workToSelect);
                          handleWorkSelect(workToSelect);
                        }
                      }
                    }}
                  />
                )}
              </Container>

              {/* Right panel - Metadata display and editing */}
              <SpaceBetween size="l">
                {isLoading && selectedWork ? (
                  <Container>
                    <Box textAlign="center" padding="l">
                      <SpaceBetween size="s" direction="vertical" alignItems="center">
                        <Spinner />
                        <Box variant="p">Loading metadata details...</Box>
                      </SpaceBetween>
                    </Box>
                  </Container>
                ) : selectedWork && metadata ? (
                  <>
                    <Container
                      header={
                        <Header
                          variant="h2"
                          actions={
                            <Button
                              variant="primary"
                              disabled={Object.keys(modifiedFields).length === 0}
                              onClick={updateMetadata}
                            >
                              Save Changes
                            </Button>
                          }
                        >
                          Document Preview
                        </Header>
                      }
                    >
                      <Grid
                        gridDefinition={
                          metadata.image_s3_uris.length === 1
                            ? [{ colspan: 12 }]
                            : [
                                { colspan: { default: 12, xxs: 6 } },
                                { colspan: { default: 12, xxs: 6 } }
                              ]
                        }
                      >
                        {metadata?.image_s3_uris?.slice(0, 2).map((uri, index) => (
                          <div
                            key={uri}
                            style={{
                              padding: '1rem',
                              textAlign: 'center',
                              margin: metadata.image_s3_uris.length === 1 ? '0 auto' : '0'  // Center if single image
                            }}
                          >
                            {imageData[uri] ? (
                              <img
                                src={imageData[uri]}
                                alt={`Page ${index + 1}`}
                                style={{
                                  maxWidth: '100%',
                                  maxHeight: '400px',
                                  objectFit: 'contain',
                                  border: '1px solid #eaeded',
                                  borderRadius: '4px',
                                  padding: '8px',
                                  boxShadow: '0 1px 2px rgba(0, 0, 0, 0.05)'
                                }}
                              />
                            ) : (
                              <Box
                                padding="xl"
                                textAlign="center"
                                color="text-status-inactive"
                                fontSize="heading-m"
                                className="custom-document-placeholder"
                              >
                                <SpaceBetween size="s" direction="vertical" alignItems="center">
                                  <Spinner />
                                  <Box variant="p">Loading image {index + 1}...</Box>
                                </SpaceBetween>
                              </Box>
                            )}
                          </div>
                        ))}
                      </Grid>
                    </Container>

                    {/* Metadata fields */}
                    <Container
                      header={
                        <Header variant="h2">
                          Document Metadata
                        </Header>
                      }
                    >
                      <SpaceBetween size="l">
                        {Object.entries(metadata).map(([key, value]) =>
                          renderMetadataSection(key, value)
                        )}
                      </SpaceBetween>
                    </Container>
                    </>
                ) : (
                  <Container>
                    <Box textAlign="center" padding="xl">
                      <Box variant="h3">Select a document</Box>
                      <Box variant="p">
                        Please select a document from the list to view and edit its metadata.
                      </Box>
                    </Box>
                  </Container>
                )}
              </SpaceBetween>
            </Grid>
          </SpaceBetween>
        </ContentLayout>
      }
    />
    ); }

    export default Metadata;

