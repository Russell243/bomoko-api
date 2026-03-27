import { useState } from 'react';
import { Alert, StyleSheet, Switch, Text, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import api from '../../../utils/api';

export default function SetupDiscreetScreen() {
  const [shakeToTrigger, setShakeToTrigger] = useState(false);
  const [audioRecordingEnabled, setAudioRecordingEnabled] = useState(true);
  const [loading, setLoading] = useState(false);

  const saveDiscreetSettings = async () => {
    setLoading(true);
    try {
      await api.put('/sos/settings/discreet/', {
        shake_to_trigger: shakeToTrigger,
        power_button_trigger: false,
        audio_recording_enabled: audioRecordingEnabled,
      });
      router.push('/(auth)/setup/language');
    } catch {
      Alert.alert('Erreur', "Impossible d'enregistrer les parametres discrets.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Setup 2/3 - Mode discret</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Activer secousse pour SOS</Text>
        <Switch value={shakeToTrigger} onValueChange={setShakeToTrigger} />
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Enregistrement audio d'urgence</Text>
        <Switch value={audioRecordingEnabled} onValueChange={setAudioRecordingEnabled} />
      </View>
      <TouchableOpacity style={styles.button} onPress={saveDiscreetSettings} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? 'Enregistrement...' : 'Continuer'}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5', padding: 20, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: '900', color: '#1C1E21', marginBottom: 18 },
  row: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E4E6EB',
    padding: 12,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  label: { color: '#1C1E21', fontWeight: '600', flex: 1, marginRight: 10 },
  button: { backgroundColor: '#1877F2', borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 8 },
  buttonText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: 16 },
});
