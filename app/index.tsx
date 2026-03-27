import { Redirect } from 'expo-router';
import { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { getAuthToken } from '../utils/api';

export default function Index() {
  const [targetRoute, setTargetRoute] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    const checkAuth = async () => {
      const token = await getAuthToken();
      if (!isMounted) return;
      setTargetRoute(token ? '/(tabs)' : '/(auth)/welcome');
    };
    checkAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  if (!targetRoute) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#E53E3E" />
      </View>
    );
  }

  return <Redirect href={targetRoute as any} />;
}
