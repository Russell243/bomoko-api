import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = 'bomoko_offline_queue_v1';
const MAX_QUEUE_SIZE = 100;

export type OfflineQueueItem = {
  type: 'sos_location';
  alertId: string;
  payload: {
    latitude: number;
    longitude: number;
  };
  createdAt: number;
};

const readWeb = (): OfflineQueueItem[] => {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.sessionStorage.getItem(KEY) ?? window.localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

const writeWeb = (items: OfflineQueueItem[]) => {
  if (typeof window === 'undefined') return;
  try {
    window.sessionStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    window.localStorage.setItem(KEY, JSON.stringify(items));
  }
};

export const getOfflineQueue = async (): Promise<OfflineQueueItem[]> => {
  if (Platform.OS === 'web') return readWeb();
  const raw = await AsyncStorage.getItem(KEY);
  return raw ? JSON.parse(raw) : [];
};

export const setOfflineQueue = async (items: OfflineQueueItem[]) => {
  if (Platform.OS === 'web') {
    writeWeb(items);
    return;
  }
  await AsyncStorage.setItem(KEY, JSON.stringify(items));
};

export const enqueueLocationUpdate = async (alertId: string, payload: { latitude: number; longitude: number }) => {
  const items = await getOfflineQueue();
  items.push({
    type: 'sos_location',
    alertId,
    payload,
    createdAt: Date.now(),
  });
  await setOfflineQueue(items.slice(-MAX_QUEUE_SIZE));
};

export const flushOfflineQueue = async (sender: (item: OfflineQueueItem) => Promise<void>) => {
  const items = await getOfflineQueue();
  if (!items.length) return;

  const remaining: OfflineQueueItem[] = [];
  for (const item of items) {
    try {
      await sender(item);
    } catch {
      remaining.push(item);
    }
  }
  await setOfflineQueue(remaining);
};
