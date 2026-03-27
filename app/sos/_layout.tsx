import { Stack } from 'expo-router';

export default function SosStackLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerTitleStyle: { fontWeight: '700' },
      }}
    />
  );
}
