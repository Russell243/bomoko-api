import React, { useState } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ScrollView, Alert } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api, { setAuthToken, setRefreshToken } from '../../utils/api';

export default function LoginScreen() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    const normalizedPhone = phone.trim();
    if (!normalizedPhone || !password) {
      Alert.alert('Erreur', 'Veuillez saisir vos identifiants.');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/users/login/', {
        username: normalizedPhone,
        password: password,
      });

      const { access, refresh } = response.data;
      await setAuthToken(access);
      await setRefreshToken(refresh);
      router.replace('/(tabs)');
    } catch (error: any) {
      const msg = error.response?.status === 401
        ? 'Identifiants incorrects.'
        : error.response?.status === 429
          ? 'Trop de tentatives. Reessayez plus tard.'
          : 'Une erreur est survenue lors de la connexion.';
      Alert.alert('Erreur', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#2D3748" />
        </TouchableOpacity>

        <View style={styles.header}>
          <Text style={styles.brand}>bomoko</Text>
          <Text style={styles.title}>Connexion</Text>
          <Text style={styles.subtitle}>Accedez a votre compte en toute securite.</Text>
        </View>

        <View style={styles.formCard}>
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Numero de telephone</Text>
            <View style={styles.inputWrapper}>
              <Ionicons name="call-outline" size={20} color="#718096" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="+243 000 000 000"
                keyboardType="phone-pad"
                value={phone}
                onChangeText={setPhone}
              />
            </View>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Mot de passe</Text>
            <View style={styles.inputWrapper}>
              <Ionicons name="lock-closed-outline" size={20} color="#718096" style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="........"
                secureTextEntry
                value={password}
                onChangeText={setPassword}
              />
            </View>
          </View>

          <TouchableOpacity style={styles.forgotPassword}>
            <Text style={styles.forgotPasswordText}>Mot de passe oublie ?</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={loading}>
            <Text style={styles.loginButtonText}>{loading ? 'Connexion...' : 'Se connecter'}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Pas encore de compte ? </Text>
          <TouchableOpacity onPress={() => router.push('/(auth)/register')}>
            <Text style={styles.footerActionText}>Creer un compte</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5' },
  scrollContent: { flexGrow: 1, padding: 24 },
  backButton: {
    marginTop: 40,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: { marginTop: 16, marginBottom: 18, alignItems: 'center' },
  brand: { fontSize: 42, fontWeight: '900', color: '#1877F2', letterSpacing: -1 },
  title: { fontSize: 28, fontWeight: '900', color: '#1C1E21', marginTop: 8 },
  subtitle: { fontSize: 16, color: '#4B4F56', marginTop: 8, textAlign: 'center' },
  formCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E4E6EB',
    padding: 16,
  },
  inputGroup: { marginBottom: 16 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#4A5568', marginBottom: 8 },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F7FAFC',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CCD0D5',
    paddingHorizontal: 12,
  },
  inputIcon: { marginRight: 10 },
  input: { flex: 1, height: 50, fontSize: 16, color: '#2D3748' },
  forgotPassword: { alignSelf: 'flex-end', marginBottom: 18 },
  forgotPasswordText: { color: '#1877F2', fontWeight: 'bold', fontSize: 14 },
  loginButton: {
    backgroundColor: '#1877F2',
    height: 52,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginButtonText: { color: '#FFFFFF', fontSize: 18, fontWeight: 'bold' },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: 20, marginBottom: 24 },
  footerText: { color: '#606770', fontSize: 15 },
  footerActionText: { color: '#1877F2', fontWeight: 'bold', fontSize: 15 },
});
