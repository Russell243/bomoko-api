import { Stack, useRouter, useSegments } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, Linking, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import api, { getAuthToken } from '../utils/api';
import {
  ensureSosShortcutNotification,
  initializeNotificationListeners,
  registerForPushNotificationsAsync,
} from '../utils/notifications';

export default function RootLayout() {
  const segments = useSegments();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const checkAuth = async () => {
      const token = await getAuthToken();
      const inAuthGroup = segments[0] === '(auth)';
      const authScreen = (segments as string[])[1] ?? '';
      const isPostRegisterFlow = inAuthGroup && (authScreen === 'verify-otp' || authScreen === 'setup');

      if (!token && !inAuthGroup) {
        router.replace('/(auth)/welcome');
      } else if (!token && isPostRegisterFlow) {
        router.replace('/(auth)/login');
      } else if (token && inAuthGroup && !isPostRegisterFlow) {
        router.replace('/(tabs)');
      }
      if (!cancelled) {
        setIsReady(true);
      }
    };
    checkAuth();
    return () => {
      cancelled = true;
    };
  }, [segments, router]);

  useEffect(() => {
    const syncPushToken = async () => {
      const token = await getAuthToken();
      if (!token) return;
      const expoToken = await registerForPushNotificationsAsync();
      if (!expoToken) return;

      try {
        await api.put('/users/profile/', {
          profile: {
            firebase_token: expoToken,
          },
        });
      } catch {
        // Ignore push token sync errors in dev.
      }
    };

    syncPushToken();
  }, []);

  useEffect(() => {
    const syncOfflineQueue = async () => {
      try {
        const { flushOfflineQueue } = await import('../utils/offlineQueue');
        await flushOfflineQueue(async (item) => {
          if (item.type === 'sos_location') {
            await api.post(`/sos/alerts/${item.alertId}/location/`, item.payload);
          }
        });
      } catch {
        // Ignored
      }
    };
    
    syncOfflineQueue();
  }, []);

  useEffect(() => {
    const initShortcut = async () => {
      await ensureSosShortcutNotification();
    };

    initShortcut();

    const cleanup = initializeNotificationListeners(undefined, async (response) => {
      const action = response.actionIdentifier;
      if (action !== 'TRIGGER_SOS') return;
      router.push('/(tabs)/sos');
    });
    return cleanup;
  }, [router]);

  const handleQuickExit = async () => {
    try {
      await Linking.openURL('https://news.google.com');
    } catch {
      // no-op
    }
  };

  if (!isReady) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color="#E53E3E" />
      </View>
    );
  }

  return (
    <View style={styles.root}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="sos" />
      </Stack>

      <TouchableOpacity style={styles.quickExitButton} activeOpacity={0.9} onPress={handleQuickExit}>
        <Text style={styles.quickExitText}>Sortie rapide</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  quickExitButton: {
    position: 'absolute',
    right: 14,
    top: 52,
    zIndex: 9999,
    backgroundColor: '#1D4ED8',
    borderRadius: 20,
    paddingVertical: 10,
    paddingHorizontal: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.22,
    shadowRadius: 6,
    elevation: 8,
  },
  quickExitText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 12,
    letterSpacing: 0.2,
  },
});
