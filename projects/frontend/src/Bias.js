import React, { useState, useCallback, useEffect } from 'react';
import { useAuth } from "react-oidc-context";
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { fromCognitoIdentityPool } from "@aws-sdk/credential-provider-cognito-identity";
import { CognitoIdentityClient } from "@aws-sdk/client-cognito-identity";
import { 
  View, Card, Button, Heading, Flex, Text, Alert, Loader, Collection, ScrollView,
  Badge
} from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

function Bias() {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const { jobName, workId } = location.state || {};
  const [selectedWork, setSelectedWork] = useState(null);
  const [selectedBias, setSelectedBias] = useState(null);
  const [biasData, setBiasData] = useState(null);
  const [error, setError] = useState(null);
  const [imageData, setImageData] = useState({});
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

    const fetchBiasDetails = useCallback(async (workId) => {
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
          throw new Error(`Failed to fetch bias details: ${response.status}`);
        }
    
        const data = await response.json();
        console.log('Bias details response:', data);
        return data.item.bias_analysis; 
      } catch (err) {
        console.error('Error fetching bias details:', err);
        throw err;
      }
    }, [jobName]);
    

  const handleWorkSelect = useCallback(async (work) => {
    setIsLoading(true);
    setSelectedWork(work);
    setSelectedBias(null);
    setBiasData(null);
    setError(null);

    try {
      const biasEntries = await fetchBiasDetails(work.work_id);
      setBiasData(biasEntries);

      if (work.image_s3_uris && work.image_s3_uris.length > 0) {
        const imagePromises = work.image_s3_uris.map(async uri => {
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
      setError(`Failed to load bias details: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [fetchBiasDetails, fetchImage]);

  const handleBiasSelect = (biasEntry) => {
    setSelectedBias(biasEntry);
  };

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
  }, [auth.user?.access_token, jobName, API_ENDPOINT]);

  const getBiasLevelColor = (level) => {
    switch (level.toLowerCase()) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'grey';
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
            <Heading level={4}>Bias Analysis for {jobName}</Heading>
          </Flex>

          {error && <Alert variation="error">{error}</Alert>}

          <Flex direction="row" gap="medium">
            {/* Left Panel */}
            <Card variation="outlined" width="320px">
              <Flex direction="column" gap="medium">
                <Flex justifyContent="space-between" alignItems="center">
                  <Heading level={5}>
                    {selectedWork ? 'Bias Entries' : 'Works'}
                  </Heading>
                  {selectedWork && (
                    <Button
                      onClick={() => {
                        setSelectedWork(null);
                        setSelectedBias(null);
                        setBiasData(null);
                      }}
                      variation="link"
                    >
                      ← Back to Works
                    </Button>
                  )}
                </Flex>
                {selectedWork ? (
                  // Show bias entries for selected work
                  <Collection
                    type="list"
                    items={biasData || []}
                    gap="small"
                  >
                    {(biasEntry) => (
                      <Button
                        key={`${biasEntry.bias_type}-${biasEntry.bias_level}`}
                        onClick={() => handleBiasSelect(biasEntry)}
                        variation={selectedBias === biasEntry ? "primary" : "default"}
                        style={{
                          textAlign: 'left',
                          justifyContent: 'flex-start',
                          width: '100%',
                          padding: '12px'
                        }}
                      >
                        <Flex direction="column" gap="small">
                          <Text fontWeight="bold">{biasEntry.bias_type}</Text>
                          <Badge
                            backgroundColor={getBiasLevelColor(biasEntry.bias_level)}
                            color="white"
                          >
                            {biasEntry.bias_level} Risk
                          </Badge>
                        </Flex>
                      </Button>
                    )}
                  </Collection>
                ) : (
                  <Collection
                    type="list"
                    items={allWorks}
                    gap="small"
                  >
                    {(work) => (
                      <Button
                        key={work.work_id}
                        onClick={() => handleWorkSelect(work)}
                        variation="default"
                        style={{
                          textAlign: 'left',
                          justifyContent: 'flex-start',
                          width: '100%',
                          padding: '12px'
                        }}
                      >
                        <Text>Work ID: {work.work_id}</Text>
                      </Button>
                    )}
                  </Collection>
                )}
              </Flex>
            </Card>

            {/* Right Panel */}
            <Card variation="outlined" flex="1">
              <Flex direction="column" gap="medium">
                {isLoading ? (
                  <Flex direction="column" alignItems="center" justifyContent="center" height="600px">
                    <Loader size="large" />
                    <Text>Loading...</Text>
                  </Flex>
                ) : selectedBias ? (
                  <Card variation="outlined" padding="medium">
                    <Flex direction="column" gap="medium">
                      <Heading level={4}>{selectedBias.bias_type} Bias Analysis</Heading>
                      <Badge
                        backgroundColor={getBiasLevelColor(selectedBias.bias_level)}
                        color="white"
                        size="large"
                      >
                        {selectedBias.bias_level} Risk Level
                      </Badge>
                      <Card variation="outlined" padding="medium">
                        <Text fontWeight="bold">Explanation:</Text>
                        <Text>{selectedBias.explanation}</Text>
                      </Card>
                    </Flex>
                  </Card>
                ) : selectedWork ? (
                  <Flex direction="column" alignItems="center" justifyContent="center" height="400px">
                    <Text>Select a bias entry to view details</Text>
                  </Flex>
                ) : (
                  <Flex direction="column" alignItems="center" justifyContent="center" height="400px">
                    <Text>Select a work to view bias analysis</Text>
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

export default Bias;
