import { useState } from 'react';
import { Alert, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import api from '../../../utils/api';

const LANGUAGES = [
  { value: 'fr', label: 'Francais' },
  { value: 'ln', label: 'Lingala' },
  { value: 'sw', label: 'Swahili' },
  { value: 'en', label: 'English' },
];

export default function SetupLanguageScreen() {
  const [selectedLanguage, setSelectedLanguage] = useState('fr');
  const [loading, setLoading] = useState(false);

  const finishSetup = async () => {
    setLoading(true);
    try {
      await api.put('/users/profile/', {
        profile: {
          preferred_language: selectedLanguage,
        },
      });
      router.replace('/(tabs)');
    } catch {
      Alert.alert('Erreur', "Impossible d'enregistrer la langue.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Setup 3/3 - Langue</Text>
      <Text style={styles.subtitle}>Choisissez votre langue principale.</Text>

      <View style={styles.optionsContainer}>
        {LANGUAGES.map((language) => {
          const isActive = language.value === selectedLanguage;
          return (
            <TouchableOpacity
              key={language.value}
              style={[styles.option, isActive && styles.optionActive]}
              onPress={() => setSelectedLanguage(language.value)}
            >
              <Text style={[styles.optionText, isActive && styles.optionTextActive]}>{language.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>

      <TouchableOpacity style={styles.button} onPress={finishSetup} disabled={loading}>
        <Text style={styles.buttonText}>{loading ? 'Finalisation...' : 'Terminer'}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5', padding: 20, justifyContent: 'center' },
  title: { fontSize: 24, fontWeight: '900', color: '#1C1E21', marginBottom: 8 },
  subtitle: { fontSize: 15, color: '#4B4F56', marginBottom: 16 },
  optionsContainer: { marginBottom: 14 },
  option: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#CCD0D5',
    paddingVertical: 12,
    paddingHorizontal: 12,
    marginBottom: 10,
  },
  optionActive: {
    borderColor: '#1877F2',
    backgroundColor: '#E7F3FF',
  },
  optionText: { color: '#1C1E21', fontSize: 16, fontWeight: '600' },
  optionTextActive: { color: '#1877F2' },
  button: { backgroundColor: '#1877F2', borderRadius: 10, paddingVertical: 12, alignItems: 'center' },
  buttonText: { color: '#FFFFFF', fontWeight: 'bold', fontSize: 16 },
});
