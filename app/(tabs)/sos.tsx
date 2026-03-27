import React, { useEffect, useRef, useState } from 'react';
import { Alert, Animated, Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import * as TaskManager from 'expo-task-manager';
import * as Location from 'expo-location';
import { Audio } from 'expo-av';
import * as Haptics from 'expo-haptics';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import api from '../../utils/api';
import { enqueueLocationUpdate, flushOfflineQueue, OfflineQueueItem } from '../../utils/offlineQueue';

const SOS_LOCATION_TASK = 'bomoko-sos-location-task';
const ACTIVE_ALERT_KEY = 'bomoko_active_alert_id';
const MIN_CONTACTS_REQUIRED = 3;
const BACKGROUND_UPDATE_INTERVAL_MS = 60000;
const BACKGROUND_DISTANCE_METERS = 25;

const getWebStorage = () => {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch {
    try {
      return window.localStorage;
    } catch {
      return null;
    }
  }
};

const getActiveAlertId = async (): Promise<string | null> => {
  if (Platform.OS === 'web') {
    return getWebStorage()?.getItem(ACTIVE_ALERT_KEY) ?? null;
  }
  return AsyncStorage.getItem(ACTIVE_ALERT_KEY);
};

const setActiveAlertId = async (alertId: string | null) => {
  if (Platform.OS === 'web') {
    const storage = getWebStorage();
    if (!storage) return;
    if (alertId) storage.setItem(ACTIVE_ALERT_KEY, alertId);
    else storage.removeItem(ACTIVE_ALERT_KEY);
    return;
  }
  if (alertId) {
    await AsyncStorage.setItem(ACTIVE_ALERT_KEY, alertId);
  } else {
    await AsyncStorage.removeItem(ACTIVE_ALERT_KEY);
  }
};

const sendLocationWithOfflineFallback = async (alertId: string, latitude: number, longitude: number) => {
  try {
    await api.post(`/sos/alerts/${alertId}/location/`, { latitude, longitude });
  } catch {
    await enqueueLocationUpdate(alertId, { latitude, longitude });
  }
};

const flushPendingLocations = async () => {
  await flushOfflineQueue(async (item: OfflineQueueItem) => {
    await api.post(`/sos/alerts/${item.alertId}/location/`, item.payload);
  });
};

if (Platform.OS !== 'web' && !TaskManager.isTaskDefined(SOS_LOCATION_TASK)) {
  TaskManager.defineTask(SOS_LOCATION_TASK, async ({ data, error }) => {
    if (error) return;
    const alertId = await getActiveAlertId();
    if (!alertId) return;

    const locations = (data as { locations?: Location.LocationObject[] } | undefined)?.locations ?? [];
    for (const point of locations) {
      await sendLocationWithOfflineFallback(alertId, point.coords.latitude, point.coords.longitude);
    }

    await flushPendingLocations();
  });
}

export default function SOSScreen() {
  const [isAlertActive, setIsAlertActive] = useState(false);
  const [currentAlertId, setCurrentAlertId] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [contactsCount, setContactsCount] = useState(0);
  const [contactsLoaded, setContactsLoaded] = useState(false);
  const [audioRecordingEnabled, setAudioRecordingEnabled] = useState(true);
  const [audioRecordingState, setAudioRecordingState] = useState<'idle' | 'recording' | 'uploading'>('idle');
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const recordingRef = useRef<Audio.Recording | null>(null);

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: isAlertActive ? 1 : 1.08,
          duration: 900,
          useNativeDriver: Platform.OS !== 'web',
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: Platform.OS !== 'web',
        }),
      ])
    ).start();
  }, [isAlertActive, pulseAnim]);

  useEffect(() => {
    const bootstrapActiveAlert = async () => {
      const storedAlertId = await getActiveAlertId();
      if (storedAlertId) {
        setCurrentAlertId(storedAlertId);
        setIsAlertActive(true);
      }
    };
    bootstrapActiveAlert();
  }, []);

  useEffect(() => {
    const loadContacts = async () => {
      try {
        const response = await api.get('/sos/contacts/');
        const payload = response.data;
        const count = Array.isArray(payload)
          ? payload.length
          : Array.isArray(payload?.results)
            ? payload.results.length
            : 0;
        setContactsCount(count);
      } catch {
        setContactsCount(0);
      } finally {
        setContactsLoaded(true);
      }
    };

    loadContacts();
  }, []);

  useEffect(() => {
    const loadDiscreetSettings = async () => {
      try {
        const response = await api.get('/sos/settings/discreet/');
        setAudioRecordingEnabled(response?.data?.audio_recording_enabled !== false);
      } catch {
        setAudioRecordingEnabled(true);
      }
    };
    loadDiscreetSettings();
  }, []);

  useEffect(() => {
    if (!isAlertActive) return;

    const timer = setInterval(() => {
      flushPendingLocations().catch(() => undefined);
    }, BACKGROUND_UPDATE_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [isAlertActive]);

  useEffect(() => {
    return () => {
      const cleanupAudio = async () => {
        if (!recordingRef.current) return;
        try {
          await recordingRef.current.stopAndUnloadAsync();
        } catch {
          // ignore cleanup errors on unmount
        } finally {
          recordingRef.current = null;
          setAudioRecordingState('idle');
        }
      };
      cleanupAudio();
    };
  }, []);

  const getCurrentPosition = async (): Promise<{ lat: number; lng: number } | null> => {
    if (Platform.OS === 'web') {
      if (typeof navigator === 'undefined' || !navigator.geolocation) {
        setLocationError('Geolocalisation indisponible.');
        return null;
      }
      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({ lat: position.coords.latitude, lng: position.coords.longitude });
          },
          () => {
            setLocationError('Permission GPS refusee.');
            resolve(null);
          },
          { enableHighAccuracy: true, timeout: 10000 }
        );
      });
    }

    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocationError('Permission GPS refusee.');
        return null;
      }
      const point = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      return { lat: point.coords.latitude, lng: point.coords.longitude };
    } catch {
      setLocationError('GPS indisponible.');
      return null;
    }
  };

  const startBackgroundTracking = async () => {
    if (Platform.OS === 'web') return;

    const foreground = await Location.requestForegroundPermissionsAsync();
    if (foreground.status !== 'granted') return;

    const background = await Location.requestBackgroundPermissionsAsync();
    if (background.status !== 'granted') return;

    const alreadyStarted = await Location.hasStartedLocationUpdatesAsync(SOS_LOCATION_TASK);
    if (alreadyStarted) return;

    await Location.startLocationUpdatesAsync(SOS_LOCATION_TASK, {
      accuracy: Location.Accuracy.Balanced,
      timeInterval: BACKGROUND_UPDATE_INTERVAL_MS,
      distanceInterval: BACKGROUND_DISTANCE_METERS,
      pausesUpdatesAutomatically: false,
      foregroundService: {
        notificationTitle: 'Bomoko SOS actif',
        notificationBody: 'Votre position est partagee avec vos contacts.',
      },
    });
  };

  const stopBackgroundTracking = async () => {
    if (Platform.OS === 'web') return;
    const isRunning = await Location.hasStartedLocationUpdatesAsync(SOS_LOCATION_TASK);
    if (isRunning) {
      await Location.stopLocationUpdatesAsync(SOS_LOCATION_TASK);
    }
  };

  const startAutoAudioRecording = async () => {
    if (!audioRecordingEnabled || Platform.OS === 'web') return;
    if (recordingRef.current) return;

    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) return;

      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const recording = new Audio.Recording();
      await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      await recording.startAsync();
      recordingRef.current = recording;
      setAudioRecordingState('recording');
    } catch {
      setAudioRecordingState('idle');
    }
  };

  const stopAndUploadAudioRecording = async (alertId: string) => {
    if (!recordingRef.current) return;

    setAudioRecordingState('uploading');
    try {
      await recordingRef.current.stopAndUnloadAsync();
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;

      if (!uri) {
        setAudioRecordingState('idle');
        return;
      }

      const formData = new FormData();
      formData.append('audio', {
        uri,
        name: `sos-${alertId}.m4a`,
        type: 'audio/m4a',
      } as any);

      await api.post(`/sos/alerts/${alertId}/audio/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } catch {
      // Keep SOS flow resilient even if upload fails
    } finally {
      setAudioRecordingState('idle');
    }
  };

  const triggerSOS = async () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => {});
    }
    
    if (contactsCount < MIN_CONTACTS_REQUIRED) {
      if (Platform.OS !== 'web') {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning).catch(() => {});
      }
      Alert.alert(
        'SOS indisponible',
        `Ajoutez au moins ${MIN_CONTACTS_REQUIRED} contacts de confiance pour activer le bouton SOS.`
      );
      return;
    }

    const confirmAction = async () => {
      const firstPosition = await getCurrentPosition();
      if (firstPosition) setCoords(firstPosition);

      try {
        const response = await api.post('/sos/alerts/', {
          battery_level: 100,
          network_type: 'unknown',
        });

        const alertId = response.data.id;
        setCurrentAlertId(alertId);
        setIsAlertActive(true);
        await setActiveAlertId(alertId);

        if (Platform.OS !== 'web') {
           Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        }

        if (firstPosition) {
          await sendLocationWithOfflineFallback(alertId, firstPosition.lat, firstPosition.lng);
        }

        await startAutoAudioRecording();
        await startBackgroundTracking();
        await flushPendingLocations();

        Alert.alert('Alerte declenchee', 'Vos contacts sont en cours de notification.');
      } catch (error: any) {
        if (error?.response?.status === 401) {
          Alert.alert('Erreur', 'Vous devez etre connecte pour declencher une alerte SOS.');
        } else {
          Alert.alert('Erreur', "Impossible de declencher l'alerte.");
        }
      }
    };

    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined' && window.confirm("Declencher l'alerte SOS maintenant ?")) {
        await confirmAction();
      }
      return;
    }

    Alert.alert("Confirmation d'urgence", "Declencher l'alerte SOS maintenant ?", [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Declencher', style: 'destructive', onPress: () => void confirmAction() },
    ]);
  };

  const cancelSOS = async () => {
    if (!currentAlertId) return;

    const resolveAlert = async () => {
      try {
        await stopAndUploadAudioRecording(currentAlertId);
        await api.post(`/sos/alerts/${currentAlertId}/resolve/`);
      } catch {
        // keep local cleanup even if server resolve fails
      } finally {
        await stopBackgroundTracking();
        await setActiveAlertId(null);
        setCurrentAlertId(null);
        setIsAlertActive(false);
        setCoords(null);
        Alert.alert('Alerte arretee', 'Le mode urgence est desactive.');
      }
    };

    if (Platform.OS === 'web') {
      if (typeof window !== 'undefined' && window.confirm("Voulez-vous stopper le mode SOS ?")) {
        await resolveAlert();
      }
      return;
    }

    Alert.alert("Arreter l'alerte", 'Voulez-vous stopper le mode SOS ?', [
      { text: 'Annuler', style: 'cancel' },
      { text: 'Arreter', style: 'destructive', onPress: () => void resolveAlert() },
    ]);
  };

  return (
    <View style={[styles.container, isAlertActive && styles.containerActive]}>
      <Text style={styles.headerTitle}>{isAlertActive ? 'ALERTE EN COURS' : 'MODE URGENCE'}</Text>
      <Text style={styles.statusText}>
        {isAlertActive
          ? 'Votre position est partagee en continu avec vos contacts.'
          : `Appuyez sur SOS pour notifier immediatement vos contacts. (${contactsCount}/${MIN_CONTACTS_REQUIRED} contacts)`}
      </Text>

      {!isAlertActive && (
        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.secondaryAction} onPress={() => router.push('/sos/contacts')}>
            <Text style={styles.secondaryActionText}>Mes contacts</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.secondaryAction} onPress={() => router.push('/sos/audio-history')}>
            <Text style={styles.secondaryActionText}>Historique audio</Text>
          </TouchableOpacity>
        </View>
      )}

      {!isAlertActive && contactsLoaded && contactsCount < MIN_CONTACTS_REQUIRED && (
        <View style={styles.requirementBox}>
          <Text style={styles.requirementText}>
            Configurez encore {MIN_CONTACTS_REQUIRED - contactsCount} contact(s) de confiance pour activer SOS.
          </Text>
        </View>
      )}

      <View style={styles.buttonContainer}>
        <Animated.View style={[styles.outerRing, { transform: [{ scale: pulseAnim }] }]}>
          <LinearGradient
            colors={isAlertActive ? ['#991B1B', '#7F1D1D'] : ['#EF4444', '#B91C1C']}
            style={[
              styles.giantSOSButton,
              !isAlertActive && contactsLoaded && contactsCount < MIN_CONTACTS_REQUIRED && styles.giantSOSButtonDisabled,
            ]}
          >
            <TouchableOpacity
              style={styles.touchableArea}
              activeOpacity={0.8}
              disabled={!isAlertActive && contactsLoaded && contactsCount < MIN_CONTACTS_REQUIRED}
              onPress={isAlertActive ? cancelSOS : triggerSOS}
            >
              <Text style={styles.sosText}>{isAlertActive ? 'STOP' : 'SOS'}</Text>
            </TouchableOpacity>
          </LinearGradient>
        </Animated.View>
      </View>

      {isAlertActive && (
        <View style={styles.trackingInfo}>
          <Text style={styles.trackingTitle}>Suivi GPS actif</Text>
          {coords ? (
            <Text style={styles.trackingCoords}>
              {coords.lat.toFixed(4)}, {coords.lng.toFixed(4)}
            </Text>
          ) : (
            <Text style={styles.trackingCoords}>{locationError || 'Acquisition du signal GPS...'}</Text>
          )}
          <Text style={styles.trackingDesc}>Mises a jour prevues toutes les 60 secondes</Text>
          {audioRecordingEnabled && (
            <Text style={styles.trackingDesc}>
              Audio preuve: {audioRecordingState === 'recording' ? 'enregistrement en cours' : audioRecordingState === 'uploading' ? 'upload en cours' : 'inactif'}
            </Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#FFF5F5', alignItems: 'center', justifyContent: 'center' },
  containerActive: { backgroundColor: '#FEE2E2' },
  headerTitle: { fontSize: 28, fontWeight: '900', color: '#9B2C2C', marginBottom: 14, letterSpacing: 1 },
  statusText: { textAlign: 'center', color: '#B91C1C', fontSize: 16, fontWeight: '500', paddingHorizontal: 20, marginBottom: 34 },
  buttonContainer: { alignItems: 'center', justifyContent: 'center', marginBottom: 24 },
  outerRing: { width: 240, height: 240, borderRadius: 120, backgroundColor: 'rgba(220,38,38,0.14)', justifyContent: 'center', alignItems: 'center' },
  giantSOSButton: { width: 200, height: 200, borderRadius: 100, backgroundColor: '#DC2626', justifyContent: 'center', alignItems: 'center', shadowColor: '#991B1B', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.5, shadowRadius: 15, elevation: 12 },
  touchableArea: { width: '100%', height: '100%', justifyContent: 'center', alignItems: 'center', borderRadius: 100 },
  sosText: { color: '#FFFFFF', fontSize: 48, fontWeight: '900', letterSpacing: 2 },
  trackingInfo: { backgroundColor: '#FFFFFF', padding: 18, borderRadius: 12, width: '100%', alignItems: 'center', borderWidth: 1, borderColor: '#FCA5A5' },
  requirementBox: {
    backgroundColor: '#FEF3C7',
    borderColor: '#F59E0B',
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 16,
    width: '100%',
  },
  requirementText: { color: '#92400E', textAlign: 'center', fontWeight: '600' },
  actionsRow: { flexDirection: 'row', width: '100%', justifyContent: 'space-between', marginBottom: 16, gap: 8 },
  secondaryAction: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderColor: '#CBD5E1',
    borderWidth: 1,
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  secondaryActionText: { color: '#1F2937', fontWeight: '700' },
  trackingTitle: { color: '#065F46', fontWeight: '800', fontSize: 18, marginBottom: 8 },
  trackingCoords: { color: '#1F2937', fontSize: 15, fontWeight: '600', marginBottom: 4 },
  trackingDesc: { color: '#6B7280', fontSize: 13, marginTop: 4 },
  giantSOSButtonDisabled: { backgroundColor: '#9CA3AF' },
});
