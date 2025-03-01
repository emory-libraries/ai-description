/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { useState, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, HeadObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
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
  const location = useLocation();
  const navigate = useNavigate();
  const { s3Uris = [], jobName } = location.state || {};

  const [selectedUri, setSelectedUri] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [allMetadata, setAllMetadata] = useState({});

  const initializeS3Client = useCallback(() => {
    return new S3Client({
      region: "us-east-1",
      credentials: {
        accessKeyId: process.env.REACT_APP_AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.REACT_APP_AWS_SECRET_ACCESS_KEY,
      }
    });
  }, []);

  const fetchImage = async (uri) => {
    try {
      const s3Client = initializeS3Client();
      const matches = uri.match(/s3:\/\/([^/]+)\/(.+)/);
      if (!matches) {
        throw new Error('Invalid S3 URI format');
      }

      const [, bucket, key] = matches;
      const command = new GetObjectCommand({
        Bucket: bucket,
        Key: key
      });

      const response = await s3Client.send(command);

      const chunks = [];
      const reader = response.Body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
      }

      const blob = new Blob(chunks);
      const base64Image = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.readAsDataURL(blob);
      });

      setImageData(base64Image);
    } catch (err) {
      console.error('Error fetching image:', err);
      setImageData(null);
      setError(`Error fetching image: ${err.message}`);
    }
  };

  const fetchMetadata = async (uri) => {
    setIsLoading(true);
    setError(null);
    try {
      const s3Client = initializeS3Client();
      const matches = uri.match(/s3:\/\/([^/]+)\/(.+)/);
      if (!matches) {
        throw new Error('Invalid S3 URI format');
      }

      const [, bucket, key] = matches;
      const command = new HeadObjectCommand({
        Bucket: bucket,
        Key: key
      });

      const response = await s3Client.send(command);
      const metadataObj = {
        ...response.Metadata
      };

      setSelectedUri(uri);
      setMetadata(metadataObj);
      setAllMetadata(prev => ({
        ...prev,
        [uri]: metadataObj
      }));

      await fetchImage(uri);
    } catch (err) {
      setError(`Error fetching metadata: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMetadataEdit = (key, value) => {
    const updatedMetadata = {
      ...metadata,
      [key]: value
    };
    setMetadata(updatedMetadata);
    setAllMetadata(prev => ({
      ...prev,
      [selectedUri]: updatedMetadata
    }));
  };

  const downloadAllMetadata = () => {
    if (Object.keys(allMetadata).length === 0) return;

    const allKeys = new Set();
    Object.values(allMetadata).forEach(metadata => {
      Object.keys(metadata).forEach(key => allKeys.add(key));
    });
    const headers = Array.from(allKeys);

    const csvContent = [
      ['S3 URI', 'File Name', ...headers].join(','),
      ...Object.entries(allMetadata).map(([uri, metadata]) => {
        return [
          uri,
          uri.split('/').pop().split('.')[0],
          ...headers.map(header => {
            const value = metadata[header];
            return value ? `"${value.toString().replace(/"/g, '""')}"` : '';
          })
        ].join(',');
      })
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    link.href = URL.createObjectURL(blob);
    link.download = `${jobName}-results.csv`;
    link.style.display = 'none';
    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  };

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
            <Heading level={4}>Results for {jobName}</Heading>
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
                  <Collection
                    type="list"
                    items={s3Uris}
                    gap="small"
                  >
                    {(uri) => (
                      <Button
                        key={uri}
                        onClick={() => fetchMetadata(uri)}
                        variation={selectedUri === uri ? "primary" : "default"}
                        style={{
                          textAlign: 'left',
                          justifyContent: 'flex-start',
                          width: '100%'
                        }}
                      >
                        {uri.split('/').pop().split('.')[0]}
                      </Button>
                    )}
                  </Collection>
                </Flex>
              </Card>

              <Card variation="outlined" flex="2">
                <Flex direction="column" gap="medium">
                  <Flex justifyContent="space-between" alignItems="center">
                    <Heading level={5}>
                      {selectedUri ? `Data for ${selectedUri.split('/').pop().split('.')[0]}` : 'Metadata'}
                    </Heading>
                    <Button
                      variation="primary"
                      onClick={downloadAllMetadata}
                      disabled={Object.keys(allMetadata).length === 0}
                    >
                      Download All Metadata
                    </Button>
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
                        {([key, value]) => (
                          <Card
                            key={key}
                            variation="outlined"
                            padding="small"
                          >
                            <Flex direction="column" gap="small">
                              <Text fontWeight="bold">{key.replace(/-/g, ' ')}</Text>
                              <input
                                type="text"
                                value={value?.toString() || ''}
                                onChange={(e) => handleMetadataEdit(key, e.target.value)}
                                style={{
                                  padding: '8px',
                                  border: '1px solid #ccc',
                                  borderRadius: '4px',
                                  width: '100%'
                                }}
                              />
                            </Flex>
                          </Card>
                        )}
                      </Collection>
                    ) : (
                      <Text>Select an S3 URI to view metadata</Text>
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
