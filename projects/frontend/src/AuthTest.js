/*
* Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
* Terms and the SOW between the parties dated 2025.
*/

import React, { useEffect, useState } from 'react';
import { Amplify } from 'aws-amplify';
import { withAuthenticator, Button, Heading, Text, View } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';

// Amplify configuration
Amplify.configure({
  Auth: {
    region: 'us-east-1',
    userPoolId: 'us-east-1_hYxw3eUXf',
    userPoolWebClientId: '6jfjqs4afd987ok6j71gh1gqmg',
    identityPoolId: 'us-east-1:180155a3-486f-42c4-944c-bb14e1556012'
  }
});

function AuthTest({ signOut, user }) {
  const [authStatus, setAuthStatus] = useState('Checking authentication...');

  useEffect(() => {
    if (user) {
      setAuthStatus('User is signed in');
      console.log('User:', user);
    } else {
      setAuthStatus('User is not signed in');
    }
  }, [user]);

  return (
    <View className="Auth">
      <Heading level={1}>Authentication Test</Heading>
      <Text>{authStatus}</Text>
      {user && (
        <View>
          <Text>Username: {user.username}</Text>
          <Button onClick={signOut}>Sign out</Button>
        </View>
      )}
    </View>
  );
}

export default withAuthenticator(AuthTest);
