import React, { useState, useCallback, useEffect } from 'react';
import { useAuth } from "react-oidc-context";
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { fromCognitoIdentityPool } from "@aws-sdk/credential-provider-cognito-identity";
import { CognitoIdentityClient } from "@aws-sdk/client-cognito-identity";
import { 
  View, Card, Button, Heading, Flex, Text, Alert, Loader, Collection, ScrollView
} from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

function App() {
  const auth = useAuth();
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
  const API_ENDPOINT = 'https://pn17lumhd3.execute-api.us-east-1.amazonaws.com/dev';

  const initializeS3Client = useCallback(() => {
    return new S3Client({
      region: "us-east-1",
      credentials: fromCognitoIdentityPool({
        client: new CognitoIdentityClient({ region: "us-east-1" }),
        identityPoolId: process.env.REACT_APP_IDENTITY_POOL_ID,
        logins: {
          [`cognito-idp.us-east-1.amazonaws.com/${process.env.REACT_APP_COGNITO_USER_POOL_ID}`]: auth.user?.id_token
        }
      })
    });
  }, [auth.user?.id_token]);

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

  const fetchWorkDetails = useCallback(async (workId) => {
    try {
      const response = await fetch(
        `${API_ENDPOINT}/results?job_name=${jobName}&work_id=${workId}`,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch work details: ${response.status}`);
      }

      const data = await response.json();
      return data.item;
    } catch (err) {
      console.error('Error fetching work details:', err);
      throw err;
    }
  }, [jobName, API_ENDPOINT]);

  const handleWorkSelect = useCallback(async (work) => {
    setIsLoading(true);
    setSelectedWork(work);
    setMetadata(null);
    setImageData({});
    setError(null);

    try {
      const workDetails = await fetchWorkDetails(work.work_id);
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
      setError(`Failed to load work details: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [fetchWorkDetails, fetchImage]);

  useEffect(() => {
    const fetchAllWorks = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `${API_ENDPOINT}/job_progress?job_name=${jobName}`,
          {
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );

        if (!response.ok) {
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

        if (works.length > 0) {
          await handleWorkSelect(works[0]);
        }
      } catch (err) {
        console.error('Error fetching all works:', err);
        setError(`Error fetching works: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    if (auth.user?.access_token && jobName) {
      fetchAllWorks();
    }
  }, [auth.user?.access_token, jobName, API_ENDPOINT, handleWorkSelect]);

  const handleMetadataEdit = (key, value, isNestedObject = false) => {
    if (key === 'job_name' || key === 'work_id') return;
  
    let parsedValue = isNestedObject ? 
      (value.trim() === '' ? {} : JSON.parse(value)) : 
      value;
  
    setMetadata(prev => ({
      ...prev,
      [key]: parsedValue
    }));
    
    setModifiedFields(prev => ({
      ...prev,
      [key]: parsedValue
    }));
  };
  
  const updateMetadata = async () => {
    if (!auth.user?.access_token || !jobName || !selectedWork) {
      setError('Unable to update: Missing required data');
      return;
    }
  
    try {
      setIsLoading(true);
      const url = `${API_ENDPOINT}/results`;
      
      if (Object.keys(modifiedFields).length === 0) {
        setError('No fields have been modified');
        return;
      }
  
      const requestBody = {
        job_name: jobName,
        work_id: selectedWork.work_id,
        updated_fields: modifiedFields
      };
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${auth.user.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
  
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
  
      const data = await response.json();
      setMetadata(data.item);
      setModifiedFields({});
      setError(null);
    } catch (err) {
      console.error('Error updating metadata:', err);
      setError(`Error updating metadata: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadAllMetadata = async () => {
    if (!allWorks || allWorks.length === 0) {
      setError('No works available to download');
      return;
    }
  
    try {
      setIsLoading(true);
      setError(`Preparing download for ${allWorks.length} works...`);
  
      const allMetadataResults = [];
      for (let i = 0; i < allWorks.length; i++) {
        const work = allWorks[i];
        setError(`Fetching data for work ${i + 1} of ${allWorks.length}...`);
        
        try {
          const metadata = await fetchWorkDetails(work.work_id);
          allMetadataResults.push({
            ...metadata
          });
        } catch (err) {
          console.error(`Error fetching work ${work.work_id}:`, err);
          allMetadataResults.push({
            error: 'Failed to fetch metadata'
          });
        }
      }
  
      const allKeys = new Set();
      allMetadataResults.forEach(metadata => {
        Object.keys(metadata).forEach(key => {
          if (key !== 'image_s3_uris') { 
            allKeys.add(key);
          }
        });
      });
  
      const headers = [
        'work_id',
        'work_status',
        ...Array.from(allKeys).filter(key => 
          !['work_id', 'work_status'].includes(key)
        )
      ];
  
      const rows = allMetadataResults.map(metadata => {
        return headers.map(header => {
          const value = metadata[header];
          if (value === undefined || value === null) {
            return '""';
          }
          if (typeof value === 'object') {
            try {
              const jsonValue = typeof value === 'string' ? JSON.parse(value) : value;
              if (Array.isArray(jsonValue)) {
                return `"${jsonValue.join(', ')}"`;
              } else {
                const readableValue = Object.entries(jsonValue)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(', ');
                return `"${readableValue.replace(/"/g, '""')}"`;
              }
            } catch (e) {
              return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
            }
          }
          if (typeof value === 'string' && value.startsWith('{')) {
            try {
              const jsonValue = JSON.parse(value);
              if (Array.isArray(jsonValue)) {
                return `"${jsonValue.join(', ')}"`;
              } else {
                const readableValue = Object.entries(jsonValue)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join('; ');
                return `"${readableValue.replace(/"/g, '""')}"`;
              }
            } catch (e) {
              return `"${String(value).replace(/"/g, '""')}"`;
            }
          }
          return `"${String(value).replace(/"/g, '""')}"`;
        }).join(',');
      });

      const csvContent = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `${jobName}-all-results-${new Date().toISOString()}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
  
      setError(null);
    } catch (error) {
      console.error('Error downloading all metadata:', error);
      setError(`Error downloading all metadata: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };
  

  return (
    <View padding="medium">
      <Card variation="elevated">
        <Flex direction="column" gap="medium">
          <Flex justifyContent="space-between" alignItems="center">
            <Button onClick={() => navigate('/')} variation="link">
              ← Back to Jobs
            </Button>
            <Heading level={4}>Results for {jobName}</Heading>
          </Flex>

          {error && <Alert variation="error">{error}</Alert>}

          <Flex direction="row" gap="medium">
            <Card variation="outlined" width="320px">
              <Flex direction="column" gap="medium">
                <Flex direction="row" alignItems="center" justifyContent="space-between">
                  <Heading level={5}>Works</Heading>
                  <Flex justifyContent = "flex-end" gap = "small">
                    <Button
                      variation="primary"
                      size="small"
                      onClick={downloadAllMetadata}
                      style={{
                        padding: '4px',  
                        fontSize: '0.875rem', 
                        height: '32px',
                        width: '180px'   
                      }}
                    >
                      {isLoading ? 'Preparing Download...' : 'Download All Metadata'}
                    </Button>
                  </Flex>
                </Flex>
                {allWorks.length > 0 ? (
                  <Collection
                    type="list"
                    items={allWorks}
                    gap="small"
                  >
                    {(work) => (
                      <Button
                        key={work.work_id}
                        onClick={() => handleWorkSelect(work)}
                        variation={selectedWork?.work_id === work.work_id ? "primary" : "default"}
                        style={{
                          textAlign: 'left',
                          justifyContent: 'flex-start',
                          width: '100%',
                          padding: '12px'
                        }}
                      >
                        <Flex direction="column" gap="small">
                          <Text>Work ID: {work.work_id}</Text>
                          <Text 
                            fontSize="small" 
                            color={work.work_status === 'FAILED TO PROCESS' ? 'red' : 'gray'}
                          >
                            Status: {work.work_status}
                          </Text>
                        </Flex>
                      </Button>
                    )}
                  </Collection>
                ) : (
                  <Text>No works available</Text>
                )}
              </Flex>
            </Card>

            <Card variation="outlined" flex="1">
              <Flex direction="column" gap="medium">
                {isLoading ? (
                  <Flex direction="column" alignItems="center" justifyContent="center">
                    <Loader size="large" />
                    <Text>Loading work details...</Text>
                  </Flex>
                ) : selectedWork ? (
                  <>
                    <Flex justifyContent="flex-end" gap="small">
                      <Button
                        variation="primary"
                        size = "small"
                        onClick={updateMetadata}
                        disabled={!metadata || isLoading || Object.keys(modifiedFields).length === 0}
                      >
                        Update Metadata
                      </Button>
                    </Flex>

                    <Card variation="outlined" padding="medium">
                      <Flex direction="row" gap="medium" justifyContent="center">
                        {metadata?.image_s3_uris?.slice(0, 2).map((uri, index) => (
                          <Card 
                            key={uri} 
                            variation="outlined" 
                            padding="small"
                            backgroundColor="white"
                            width="400px"
                            height="400px"
                          >
                            <Flex 
                              direction="column" 
                              alignItems="center" 
                              justifyContent="center"
                              height="100%"
                            >
                              {imageData[uri] ? (
                                <img
                                  src={imageData[uri]}
                                  alt={`Image ${index + 1}`}
                                  style={{
                                    width: '100%',
                                    height: '100%',
                                    objectFit: 'contain'
                                  }}
                                />
                              ) : (
                                <Flex 
                                  direction="column" 
                                  alignItems="center" 
                                  justifyContent="center"
                                  height="100%"
                                  width="100%"
                                >
                                  <Loader size="large" />
                                  <Text>Loading image {index + 1}...</Text>
                                </Flex>
                              )}
                            </Flex>
                          </Card>
                        ))}
                      </Flex>
                    </Card>

                    {metadata ? (
                      <ScrollView height="400px">
                        <Collection
                          type="list"
                          items={Object.entries(metadata)}
                          gap="small"
                        >
                          {([key, value]) => {
                            if (key === 'image_s3_uris' || key === 'work_id' || 
                                key === 'job_name' || key === 'work_status') {
                              return null;
                            }

                            const isObject = typeof value === 'object' && value !== null;
                            const displayValue = isObject ? 
                              JSON.stringify(value, null, 2) : 
                              String(value || '');

                            return (
                              <Card
                                key={key}
                                variation="outlined"
                                padding="small"
                              >
                                <Flex direction="column" gap="small">
                                  <Text fontWeight="bold">
                                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </Text>
                                  <textarea
                                    value={isObject ? 
                                      (() => {
                                        try {
                                          if (Array.isArray(value)) {
                                            return value.join(', ');
                                          } else {
                                            return Object.entries(value)
                                              .map(([k, v]) => `${k}: ${v}`)
                                              .join(', ');
                                          }
                                        } catch (e) {
                                          return typeof value === 'string' ? value : JSON.stringify(value, null, 2);
                                        }
                                      })()
                                      : displayValue
                                    }
                                    onChange={(e) => handleMetadataEdit(key, e.target.value, isObject)}
                                    placeholder={`Enter ${key.replace(/_/g, ' ').toLowerCase()}`}
                                    style={{
                                      padding: '8px',
                                      border: '1px solid #ccc',
                                      borderRadius: '4px',
                                      width: '100%',
                                      minHeight: '100px',
                                      resize: 'vertical',
                                      fontFamily: 'monotone',
                                      whiteSpace: 'pre-wrap'
                                    }}
                                />
                                </Flex>
                              </Card>
                            );
                          }}
                        </Collection>
                      </ScrollView>
                    ) : (
                      <Flex 
                        direction="column" 
                        alignItems="center" 
                        justifyContent="center" 
                        height="200px"
                      >
                        <Text>No metadata available</Text>
                      </Flex>
                    )}
                  </>
                ) : (
                  <Flex 
                    direction="column" 
                    alignItems="center" 
                    justifyContent="center" 
                    height="600px"
                  >
                    <Text>Select a work item to view details</Text>
                  </Flex>
                )}
              </Flex>
            </Card>
          </Flex>
        </Flex>
      </Card>
    </View>
  );
}

export default App;