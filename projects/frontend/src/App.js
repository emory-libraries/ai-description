import React, { useState, useCallback, useEffect } from 'react';
import { useAuth } from "react-oidc-context";
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { fromCognitoIdentityPool } from "@aws-sdk/credential-provider-cognito-identity";
import { CognitoIdentityClient } from "@aws-sdk/client-cognito-identity";
import { 
  View, 
  Card, 
  Button, 
  Heading, 
  Flex, 
  Text,
  Alert,
  Loader,
  Collection,
  ScrollView
} from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

function App() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { jobName, workId } = location.state || {};
  
  const [selectedUri, setSelectedUri] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [modifiedFields, setModifiedFields] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [allMetadata, setAllMetadata] = useState({});
  const [workItemData, setWorkItemData] = useState(null);
  const API_ENDPOINT = 'https://snqamgfnv4.execute-api.us-east-1.amazonaws.com/dev';

  const initializeS3Client = useCallback(() => {
    console.log('Initializing S3 client with token:', !!auth.user?.id_token);
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

  useEffect(() => {
    const fetchWorkItemData = async () => {
      if (!auth.user?.access_token || !jobName || !workId) {
        console.log('Missing requirements:', { 
          hasToken: !!auth.user?.access_token, 
          jobName,
          workId,
          locationState: location.state
        });
        return;
      }

      try {
        setIsLoading(true);
        const url = `${API_ENDPOINT}/results?job_name=${jobName}&work_id=${workId}`;
        console.log('Fetching job results from:', url);

        const response = await fetch(
          url,
          {
            headers: {
              'Authorization': `Bearer ${auth.user.access_token}`,
              'Content-Type': 'application/json'
            }
          }
        );

        console.log('API response status:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.log('Error response:', errorText);
          throw new Error(`API returned ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log('Job results data received:', data);
        console.log('S3 URIs in response:', data.item?.s3_uris); // Add this log
        
        if (data.item) {
          setWorkItemData(data.item);
          setMetadata(data.item);
          // Change s3_uris to image_s3_uris to match the new parameter name
          if (data.item.image_s3_uris && data.item.image_s3_uris.length > 0) {
            const validUris = data.item.image_s3_uris.filter(uri => 
              uri && uri.startsWith('s3://')
            );
            console.log('Valid S3 URIs:', validUris);
        
            if (validUris.length > 0) {
              setSelectedUri(validUris[0]);
              await fetchImage(validUris[0]);
            } else {
              console.error('No valid S3 URIs found in:', data.item.image_s3_uris);
              setError('No valid S3 URIs found in response');
            }
          }
        }        
      } catch (err) {
        console.error('Error fetching job results:', err);
        setError(`Error fetching data: ${err.message}`);
      } finally {
        setIsLoading(false);
      }
    };

    if (auth.user?.access_token && jobName && workId) {
      fetchWorkItemData();
    }
  }, [auth.user?.access_token, jobName, workId, location.state]);

  
  const fetchImage = async (uri) => {
    console.log('Attempting to fetch image for URI:', uri);
    
    if (!uri || typeof uri !== 'string') {
      console.error('Invalid URI provided:', uri);
      setError('Invalid S3 URI format');
      return;
    }
  
    try {
      const s3Client = initializeS3Client();
      const matches = uri.match(/s3:\/\/([^/]+)\/(.+)/);
      
      if (!matches || matches.length !== 3) {
        console.error('Invalid S3 URI format:', uri);
        throw new Error(`Invalid S3 URI format: ${uri}`);
      }
    
      const [, bucket, key] = matches;
      console.log('Parsed S3 parameters:', { bucket, key });
  
      const command = new GetObjectCommand({
        Bucket: bucket,
        Key: key
      });
    
      const response = await s3Client.send(command);
      console.log('S3 response received');
      
      const arrayBuffer = await response.Body.transformToByteArray();
      const blob = new Blob([arrayBuffer]);
      const base64Image = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });
      
      console.log('Image successfully loaded');
      setImageData(base64Image);
    } catch (err) {
      console.error('Error fetching image:', err);
      setImageData(null);
      setError(`Error fetching image: ${err.message}`);
    }
  };

  const handleUriSelect = async (uri) => {
    console.log('URI selected:', uri);
    setSelectedUri(uri);
    setError(null);
    await fetchImage(uri);
  };

  const handleMetadataEdit = (key, value, isNestedObject = false) => {
    console.log('Editing metadata:', { key, value, isNestedObject });
    
    // Don't track changes to internal fields
    if (key === 'job_name' || key === 'work_id') {
      return;
    }
  
    let parsedValue = value;
    if (isNestedObject) {
      try {
        // If empty string, set to empty object instead of null
        parsedValue = value.trim() === '' ? {} : JSON.parse(value);
      } catch (e) {
        console.warn('Failed to parse edited value as JSON:', e);
        return;
      }
    } else {
      // For non-objects, empty string is valid
      parsedValue = value;
    }
  
    const updatedMetadata = {
      ...metadata,
      [key]: parsedValue
    };
    
    setMetadata(updatedMetadata);
    setModifiedFields(prev => ({
      ...prev,
      [key]: parsedValue
    }));
    setAllMetadata(prev => ({
      ...prev,
      [selectedUri]: updatedMetadata
    }));
  };
  
  const updateMetadata = async () => {
    if (!auth.user?.access_token || !jobName || !workId) {
      console.error('Missing required data for update');
      setError('Unable to update: Missing required data');
      return;
    }
  
    try {
      setIsLoading(true);
      const url = `${API_ENDPOINT}/results`;
      
      // Make sure we have all required fields
      if (Object.keys(modifiedFields).length === 0) {
        setError('No fields have been modified');
        return;
      }
  
      const requestBody = {
        job_name: jobName,
        work_id: workId,
        updated_fields: modifiedFields
      };
      
      console.log('Sending request with body:', JSON.stringify(requestBody, null, 2));
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${auth.user.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });
  
      const responseText = await response.text();
      console.log('Raw response:', responseText);
  
      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${responseText}`);
      }
  
      const data = JSON.parse(responseText);
      console.log('Update response:', data);
      
      // Clear modified fields after successful update
      setModifiedFields({});
      
      setMetadata(data.item);
      setAllMetadata(prev => ({
        ...prev,
        [selectedUri]: data.item
      }));
      setError(null);
    } catch (err) {
      console.error('Error updating metadata:', err);
      setError(`Error updating metadata: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const downloadAllMetadata = () => {
    if (Object.keys(allMetadata).length === 0) return;
    console.log('Downloading metadata:', allMetadata);
  
    // Get all possible keys from all metadata objects
    const allKeys = new Set();
    Object.values(allMetadata).forEach(metadata => {
      Object.keys(metadata).forEach(key => {
        // Skip image_s3_uris or any other fields you want to exclude
        if (key !== 'image_s3_uris') {
          allKeys.add(key);
        }
      });
    });
  
    // Create headers, including special handling for bias_analysis
    const baseHeaders = Array.from(allKeys).filter(key => key !== 'bias_analysis');
    const headers = [
      'S3 URI',
      ...baseHeaders,
      'Bias Types',
      'Bias Levels',
      'Bias Explanations'
    ];
  
    const csvContent = [
      headers.join(','),
      ...Object.entries(allMetadata).map(([uri, metadata]) => {
        // Handle bias analysis separately
        const biasTypes = metadata.bias_analysis?.map(b => b.bias_type).join(';') || '';
        const biasLevels = metadata.bias_analysis?.map(b => b.bias_level).join(';') || '';
        const biasExplanations = metadata.bias_analysis?.map(b => b.explanation).join(';') || '';
  
        // Handle regular fields
        const baseValues = baseHeaders.map(header => {
          const value = metadata[header];
          if (typeof value === 'object' && value !== null) {
            return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
          }
          return `"${String(value || '').replace(/"/g, '""')}"`;
        });
  
        return [
          uri,
          ...baseValues,
          `"${biasTypes}"`,
          `"${biasLevels}"`,
          `"${biasExplanations}"`
        ].join(',');
      })
    ].join('\n');
  
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    link.href = URL.createObjectURL(blob);
    link.download = `${jobName}-${workId}-results.csv`;
    link.style.display = 'none';
    document.body.appendChild(link);
    
    link.click();
    
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

  useEffect(() => {
    console.log('Received navigation state:', location.state);
  }, [location.state]);
  
  useEffect(() => {
    console.log('Component state:', {
      jobName,
      workId,
      hasWorkItemData: !!workItemData,
      selectedUri,
      hasMetadata: !!metadata,
      hasImage: !!imageData,
      auth: {
        isAuthenticated: auth.isAuthenticated,
        hasToken: !!auth.user?.access_token
      }
    });
  }, [jobName, workId, workItemData, selectedUri, metadata, imageData, auth]);

  return (
    <View padding="medium">
      <Card variation="elevated">
        <Flex direction="column" gap="medium">
          <Flex justifyContent="space-between" alignItems="center">
            <Button
              onClick={() => navigate('/')}
              variation="link"
            >
              ← Back to Jobs
            </Button>
            <Heading level={4}>Results for {jobName} - {workId}</Heading>
          </Flex>

          {error && <Alert variation="error">{error}</Alert>}

          {isLoading ? (
            <Flex direction="column" alignItems="center">
              <Loader size="large" />
              <Text>Loading results...</Text>
            </Flex>
          ) : (
            <Flex direction="row" gap="medium">
              <Card variation="outlined" flex="1">
                <Flex direction="column" gap="medium">
                  <Heading level={5}>Files</Heading>
                  {workItemData?.image_s3_uris && workItemData.image_s3_uris.length > 0 ? (
                    <Collection
                      type="list"
                      items={workItemData.image_s3_uris}
                      gap="small"
                    >
                      {(uri) => {
                        const fileName = uri.split('/').pop();
                        return (
                          <Button
                            key={uri}
                            onClick={() => handleUriSelect(uri)}
                            variation={selectedUri === uri ? "primary" : "default"}
                            style={{
                              textAlign: 'left',
                              justifyContent: 'flex-start',
                              width: '100%',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}
                          >
                            {fileName}
                          </Button>
                        );
                      }}
                    </Collection>
                  ) : (
                    <Text>No files available</Text>
                  )}
                </Flex>
              </Card>


              <Card variation="outlined" flex="2">
                <Flex direction="column" gap="medium">
                  <Flex justifyContent="space-between" alignItems="center">
                      <Heading level={5}>
                        {selectedUri ? `Data for ${selectedUri.split('/').pop()}` : 'Metadata'}
                      </Heading>
                      <Flex gap="small">
                        <Button
                            variation="primary"
                            onClick={updateMetadata}
                            disabled={!metadata || isLoading || Object.keys(modifiedFields).length === 0}
                          >
                            Update Metadata
                          </Button>
                        <Button
                          variation="primary"
                          onClick={downloadAllMetadata}
                        >
                          Download All Metadata
                        </Button>
                      </Flex>
                    </Flex>

                  {imageData && (
                    <Card variation="outlined" padding="small">
                      <Flex direction="column" gap="small" alignItems="center">
                        <img 
                          src={imageData} 
                          alt="S3 Object Preview"
                          style={{
                            maxWidth: '100%',
                            maxHeight: '300px',
                            objectFit: 'contain'
                          }}
                        />
                      </Flex>
                    </Card>
                  )}

                  <ScrollView height="600px">
                    {metadata ? (
                      <Collection
                        type="list"
                        items={Object.entries(metadata)}
                        gap="small"
                      >
                        {([key, value]) => {
                          // Only skip internal routing/system fields
                          if (key === 'image_s3_uris' || key === 'work_id' || key === 'job_name' || key === 'work_status') {
                            return null;
                          }

                          // Format the value for display
                          let displayValue = value;
                          const isObject = typeof value === 'object' && value !== null;
                          
                          if (isObject) {
                            displayValue = JSON.stringify(value, null, 2);
                          } else {
                            // Show empty string for null/undefined values instead of skipping
                            displayValue = String(value || '');
                          }

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
                                  value={displayValue}
                                  onChange={(e) => handleMetadataEdit(key, e.target.value, isObject)}
                                  placeholder={`Enter ${key.replace(/_/g, ' ').toLowerCase()}`}
                                  style={{
                                    padding: '8px',
                                    border: '1px solid #ccc',
                                    borderRadius: '4px',
                                    width: '100%',
                                    minHeight: isObject ? '200px' : '40px',
                                    resize: 'vertical',
                                    fontFamily: isObject ? 'monospace' : 'inherit'
                                  }}
                                />
                              </Flex>
                            </Card>
                          );
                        }}
                      </Collection>
                    ) : (
                      <Text>Select a file to view metadata</Text>
                    )}
                  </ScrollView>
                </Flex>
              </Card>
            </Flex>
          )}
        </Flex>
      </Card>
    </View>
  );
}

export default App;