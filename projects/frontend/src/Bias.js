/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/
import React, { useState, useCallback, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { useAuth } from './AuthContext';
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
  ColumnLayout,
  Table,
  StatusIndicator,
  Grid,
  BreadcrumbGroup
} from "@cloudscape-design/components";
import { AWSSideNavigation } from './components/Navigation';

function Bias() {
  const { token, logout } = useAuth();
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
  
  // This function should be replaced with your appropriate S3 credential management
  // You'll need to implement an approach that works with your custom auth system
  const initializeS3Client = useCallback(() => {
    return new S3Client({
      region: "us-east-1",
      // You'll need to replace this with your custom credentials approach
      // This could be a token exchange, assuming a role through API, etc.
      credentials: {
        // This is a placeholder - replace with your actual implementation
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

  const fetchBiasDetails = useCallback(async (workId) => {
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
        throw new Error(`Failed to fetch bias details: ${response.status}`);
      }
  
      const data = await response.json();
      const biasEntriesWithImages = data.item.page_biases.flatMap((page, pageIndex) => 
        page.biases.map(bias => ({
          ...bias,
          bias_type: bias.type,  
          bias_level: bias.level,    
          imageUri: data.item.image_s3_uris[pageIndex]
        }))
      );
      return biasEntriesWithImages;
    } catch (err) {
      console.error('Error fetching bias details:', err);
      throw err;
    }
  }, [jobName, token, logout, navigate]);
  
  const handleWorkSelect = useCallback(async (work) => {
    if (!work || (selectedWork && work.work_id === selectedWork.work_id)) {
      return; 
    }
    
    setIsLoading(true);
    setSelectedWork(work);
    setSelectedBias(null);
    setBiasData(null);
    setError(null);
    setImageData({}); 
    
    try {
      if (!token) {
        throw new Error('No authentication token available');
      }
      
      const response = await fetch(
        `/api/results?job_name=${work.job_name}&work_id=${work.work_id}`,
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
        throw new Error(`Failed to fetch bias details: ${response.status}`);
      }

      console.log('this is the work id: ', work.work_id);
  
      const data = await response.json();
      const image_s3_uris = data.item.image_s3_uris;
      const biasEntries = data.item.page_biases.flatMap((page, pageIndex) => 
        page.biases.map(bias => ({
          ...bias,
          imageUri: image_s3_uris[pageIndex]
        }))
      );
      setBiasData(biasEntries);
      if (image_s3_uris && image_s3_uris.length > 0) {
        const imagePromises = image_s3_uris.map(async uri => {
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
  }, [fetchImage, token, logout, navigate]); 

  const handleBiasSelect = (biasEntry) => {
    setSelectedBias(biasEntry);
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
        
        if (workId) {
          const workToSelect = works.find(w => w.work_id === workId);
          if (workToSelect) {
            await handleWorkSelect(workToSelect);
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
  }, [token, jobName, workId, handleWorkSelect, logout, navigate]);

  const getBiasLevelColor = (level) => {
    if (!level) return "grey";

    switch (level.toLowerCase()) {
      case 'high': return "error";
      case 'medium': return "warning";
      case 'low': return "success";
      default: return "grey";
    }
  };

  const handleBackToBiasList = () => {
    setSelectedBias(null);
  };

  const workNavigationItems = allWorks.map(work => ({    
    type: 'link',
    text: `Work ID: ${work.work_id}`,
    href: `#${work.work_id}`,
    info: <StatusIndicator type={work.work_status === 'READY FOR REVIEW' ? 'success' : 'in-progress'} />,
  }));

  const biasTableItems = biasData || [];
  const breadcrumbItems = [
    { text: 'Document Analysis Service', href: '/' },
    { text: 'Job Status', href: '/' },
    { text: `Bias Analysis: ${jobName || ''}` }
  ];

  return (
    <AppLayout
      toolsHide={true}
      navigation={<AWSSideNavigation activeHref="/bias" />}
      breadcrumbs={<BreadcrumbGroup items={breadcrumbItems} />}
      content={
        <ContentLayout
          header={
            <Header
              variant="h1" 
              description={`Bias analysis results for the specified document set`}
              actions={
                <Button variant="link" onClick={() => navigate('/')}>
                  Back to Job Status
                </Button>
              }
            >
              Bias Analysis: {jobName}
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
              {/* Left panel - Navigation */}
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
                        const workId = detail.href.substring(1);
                        const selectedWork = allWorks.find(work => work.work_id === workId);
                        if (selectedWork) {
                          handleWorkSelect(selectedWork);
                        }
                      }
                    }}
                  />
                )}
              </Container>

              {/* Right panel - Bias details */}
              <Container 
                header={
                  <Header 
                    variant="h2"
                    actions={
                      selectedBias ? (
                        <Button onClick={handleBackToBiasList} variant="normal">
                          Back to bias list
                        </Button>
                      ) : null
                    }
                  >
                    Bias Analysis Results
                  </Header>
                }
              >
                {isLoading && selectedWork ? (
                  <Box textAlign="center" padding="l">
                    <SpaceBetween size="s" direction="vertical" alignItems="center">
                      <Spinner />
                      <Box variant="p">Loading bias details...</Box>
                    </SpaceBetween>
                  </Box>
                ) : selectedWork ? (
                  <SpaceBetween size="l">
                    {selectedBias ? (
                      <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
                        {/* Left side - Image */}
                        <Container>
                          {imageData[selectedBias.imageUri] ? (
                            <img
                              src={imageData[selectedBias.imageUri]}
                              alt="Content with detected bias"
                              style={{
                                maxWidth: '100%',
                                maxHeight: '500px',
                                objectFit: 'contain'
                              }}
                            />
                          ) : (
                            <Box textAlign="center" padding="l">
                              <SpaceBetween size="s" direction="vertical" alignItems="center">
                                <Spinner />
                                <Box variant="p">Loading image...</Box>
                              </SpaceBetween>
                            </Box>
                          )}
                        </Container>

                        {/* Right side - Bias details */}
                        <Container header={<Header variant="h3">Bias Details</Header>}>
                          <SpaceBetween size="l">
                            <ColumnLayout columns={2} variant="text-grid">
                              <div>
                                <Box variant="awsui-key-label">Type</Box>
                                <Box variant="awsui-value-large">{selectedBias.type}</Box>
                              </div>
                              <div>
                                <Box variant="awsui-key-label">Level</Box>
                                <Box>
                                  <StatusIndicator type={getBiasLevelColor(selectedBias.level)}>
                                    {selectedBias.level} Risk
                                  </StatusIndicator>
                                </Box>
                              </div>
                            </ColumnLayout>
                            <div>
                              <Box variant="awsui-key-label">Explanation</Box>
                              <Box variant="p">{selectedBias.explanation}</Box>
                            </div>
                          </SpaceBetween>
                        </Container>
                      </Grid>
                    ) : (
                      <Table
                        header={<Header variant="h3">Identified Biases</Header>}
                        columnDefinitions={[
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
                            cell: item => item.explanation
                          }
                        ]}
                        items={biasTableItems}
                        selectionType="single"
                        onSelectionChange={({ detail }) => {
                          if (detail.selectedItems.length > 0) {
                            handleBiasSelect(detail.selectedItems[0]);
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
                    )}
                  </SpaceBetween>
                ) : (
                  <Box textAlign="center" padding="l">
                    <Box variant="h3">Select a work</Box>
                    <Box variant="p">Please select a work from the list to view bias analysis results.</Box>
                  </Box>
                )}
              </Container>
            </Grid>
          </SpaceBetween>
        </ContentLayout>
      }
    />
  );
}

export default Bias;
