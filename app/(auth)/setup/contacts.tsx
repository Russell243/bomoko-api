import { useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import api from '../../../utils/api';

export default function SetupContactsScreen() {
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);

  const saveContact = async () => {
    if (!name.trim() || !phoneNumber.trim()) {
      Alert.alert('Erreur', 'Nom et telephone requis.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/sos/contacts/', {
        name,
        phone_number: phoneNumber,
      });
      router.push('/(auth)/setup/discreet');
    } catch {
      Alert.alert('Erreur', "Impossible d'enregistrer le contact.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Setup 1/3 - Contact urgence</Text>
      <TextInput style={styles.input} placeholder="Nom du contact" value={name} onChangeText={setName} />
      <TextInput
        style={styles.input}
        placeholder="+243..."
        keyboardType="phone-pad"
        value={phoneNumber}
        onChangeText={setPhoneNumber}
      />
      <TouchableOpacity style={styles.button} disabled={loading} onPress={saveContact}>
        <Text style={styles.buttonText}>{loading ? 'Enregistrement...' : 'Continuer'}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5', padding: 20, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: '900', color: '#1C1E21', marginBottom: 14 },
  input: {
    height: 48,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CCD0D5',
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
    marginBottom: 10,
  },
  button: { backgroundColor: '#1877F2', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  buttonText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: 16 },
});

