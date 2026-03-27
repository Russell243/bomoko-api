import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

const SOS_SHORTCUT_CATEGORY_ID = 'bomoko-sos-shortcut-category';
const SOS_SHORTCUT_NOTIFICATION_ID = 'bomoko-sos-shortcut-notification';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

export const registerForPushNotificationsAsync = async (): Promise<string | null> => {
  if (Platform.OS === 'web') return null;
  if (!Device.isDevice) return null;

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') return null;
  const token = await Notifications.getExpoPushTokenAsync();
  return token.data;
};

export const initializeNotificationListeners = (
  onReceive?: (notification: Notifications.Notification) => void,
  onResponse?: (response: Notifications.NotificationResponse) => void
) => {
  if (Platform.OS === 'web') {
    return () => undefined;
  }

  const receiveSub = Notifications.addNotificationReceivedListener((notification) => {
    onReceive?.(notification);
  });

  const responseSub = Notifications.addNotificationResponseReceivedListener((response) => {
    onResponse?.(response);
  });

  return () => {
    receiveSub.remove();
    responseSub.remove();
  };
};

export const ensureSosShortcutNotification = async () => {
  if (Platform.OS === 'web') return;

  await Notifications.setNotificationCategoryAsync(SOS_SHORTCUT_CATEGORY_ID, [
    {
      identifier: 'TRIGGER_SOS',
      buttonTitle: 'SOS discret',
      options: {
        opensAppToForeground: true,
      },
    },
  ]);

  const scheduled = await Notifications.getAllScheduledNotificationsAsync();
  const alreadyScheduled = scheduled.some(
    (item) => item.identifier === SOS_SHORTCUT_NOTIFICATION_ID || item.content?.data?.type === 'sos_shortcut'
  );
  if (alreadyScheduled) return;

  await Notifications.scheduleNotificationAsync({
    identifier: SOS_SHORTCUT_NOTIFICATION_ID,
    content: {
      title: 'Bomoko mode discret',
      body: 'Appuyez sur "SOS discret" pour declencher une alerte rapide.',
      categoryIdentifier: SOS_SHORTCUT_CATEGORY_ID,
      data: { type: 'sos_shortcut' },
      sticky: true,
    },
    trigger: {
      seconds: 60 * 30,
      repeats: true,
      type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
    },
  });
};
