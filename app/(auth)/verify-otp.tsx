import { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import api from '../../utils/api';

export default function VerifyOtpScreen() {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!code.trim()) {
      Alert.alert('Erreur', 'Saisissez le code OTP.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/users/verify-otp/', { code });
      Alert.alert('Succes', 'Numero verifie.');
      router.replace('/(auth)/setup/contacts');
    } catch (error: any) {
      Alert.alert('Erreur', error?.response?.data?.detail || 'Code OTP invalide.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>Verification OTP</Text>
        <Text style={styles.subtitle}>Entrez le code recu par SMS.</Text>
        <TextInput
          style={styles.input}
          value={code}
          onChangeText={setCode}
          keyboardType="number-pad"
          maxLength={6}
          placeholder="123456"
        />
        <TouchableOpacity style={styles.button} onPress={handleVerify} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? 'Verification...' : 'Verifier'}</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5', justifyContent: 'center', padding: 20 },
  card: { backgroundColor: '#FFFFFF', borderRadius: 12, borderWidth: 1, borderColor: '#E4E6EB', padding: 16 },
  title: { fontSize: 26, fontWeight: '900', color: '#1C1E21' },
  subtitle: { fontSize: 15, color: '#606770', marginTop: 8, marginBottom: 14 },
  input: {
    borderWidth: 1,
    borderColor: '#CCD0D5',
    borderRadius: 10,
    height: 48,
    paddingHorizontal: 12,
    marginBottom: 12,
    backgroundColor: '#F7FAFC',
    fontSize: 18,
    letterSpacing: 2,
  },
  button: { backgroundColor: '#1877F2', borderRadius: 10, alignItems: 'center', paddingVertical: 12 },
  buttonText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: 16 },
});

