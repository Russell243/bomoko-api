import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, ActivityIndicator, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';

export default function MedicalService() {
  const router = useRouter();
  const [bodyPart, setBodyPart] = useState('');
  const [description, setDescription] = useState('');
  const [painLevel, setPainLevel] = useState(5);
  const [severity, setSeverity] = useState('medium');
  const [loading, setLoading] = useState(false);

  const severities = [
    { key: 'low', label: 'Faible', color: '#48BB78' },
    { key: 'medium', label: 'Moyen', color: '#ECC94B' },
    { key: 'high', label: 'Élevé', color: '#ED8936' },
    { key: 'critical', label: 'Critique', color: '#E53E3E' },
  ];

  const submitReport = async () => {
    if (!description.trim()) {
      Alert.alert('Erreur', 'Veuillez décrire votre blessure ou problème.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/medical/entries/', {
        description,
        body_part: bodyPart,
        pain_level: painLevel,
        severity,
      });
      Alert.alert(
        "Signalement envoyé ✅",
        "Votre demande d'assistance médicale a été enregistrée. Un professionnel de santé vous contactera.",
        [{ text: "OK", onPress: () => router.back() }]
      );
    } catch (error: any) {
      const msg = error.response?.status === 401
        ? 'Connectez-vous pour envoyer un signalement.'
        : 'Erreur lors de l\'envoi. Vérifiez votre connexion.';
      Alert.alert('Erreur', msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
        <Ionicons name="arrow-back" size={24} color="#2D3748" />
      </TouchableOpacity>

      <View style={styles.header}>
        <Image 
          source={require('../../assets/images/professional-workers-group-doctor-man-600nw-.webp')} 
          style={styles.heroImage} 
        />
        <View style={styles.iconCircle}>
          <Ionicons name="medkit" size={40} color="#3182CE" />
        </View>
        <Text style={styles.title}>Assistance Médicale</Text>
        <Text style={styles.subtitle}>Signalez une blessure ou demandez un conseil de santé urgent.</Text>
      </View>

      <View style={styles.form}>
        <Text style={styles.label}>Partie du corps concernée</Text>
        <TextInput
          style={styles.input}
          placeholder="Ex: Bras gauche, Tête, Ventre..."
          value={bodyPart}
          onChangeText={setBodyPart}
        />

        <Text style={styles.label}>Description détaillée</Text>
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Décrivez les circonstances et l'état actuel..."
          multiline
          numberOfLines={4}
          value={description}
          onChangeText={setDescription}
        />

        <Text style={styles.label}>Niveau de douleur : {painLevel}/10</Text>
        <View style={styles.painRow}>
          {[1,2,3,4,5,6,7,8,9,10].map(n => (
            <TouchableOpacity
              key={n}
              style={[styles.painDot, painLevel === n && styles.painDotActive]}
              onPress={() => setPainLevel(n)}
            >
              <Text style={[styles.painText, painLevel === n && styles.painTextActive]}>{n}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Gravité</Text>
        <View style={styles.severityRow}>
          {severities.map(s => (
            <TouchableOpacity
              key={s.key}
              style={[styles.severityChip, severity === s.key && { backgroundColor: s.color }]}
              onPress={() => setSeverity(s.key)}
            >
              <Text style={[styles.severityText, severity === s.key && { color: '#FFF' }]}>{s.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.submitButton} onPress={submitReport} disabled={loading}>
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.submitButtonText}>Envoyer le signalement</Text>
          )}
        </TouchableOpacity>
      </View>

      <View style={styles.warningCard}>
        <Ionicons name="warning-outline" size={24} color="#9C4221" />
        <Text style={styles.warningText}>
          En cas d'urgence vitale, utilisez immédiatement le bouton SOS ou contactez les secours locaux.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFFFFF' },
  scrollContent: { padding: 24 },
  backButton: { marginTop: 20, marginBottom: 20 },
  header: { alignItems: 'center', marginBottom: 32 },
  heroImage: { width: '100%', height: 180, borderRadius: 16, marginBottom: 20 },
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#EBF8FF', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 24, fontWeight: '900', color: '#2D3748', textAlign: 'center' },
  subtitle: { fontSize: 15, color: '#718096', textAlign: 'center', marginTop: 8, lineHeight: 22 },
  form: { marginBottom: 40 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#4A5568', marginBottom: 8, marginTop: 16 },
  input: { backgroundColor: '#F7FAFC', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: '#E2E8F0', fontSize: 16 },
  textArea: { height: 120, textAlignVertical: 'top' },
  painRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  painDot: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#EDF2F7', justifyContent: 'center', alignItems: 'center' },
  painDotActive: { backgroundColor: '#E53E3E' },
  painText: { fontSize: 12, fontWeight: 'bold', color: '#718096' },
  painTextActive: { color: '#FFF' },
  severityRow: { flexDirection: 'row', gap: 8, marginTop: 8 },
  severityChip: { paddingVertical: 8, paddingHorizontal: 16, borderRadius: 20, backgroundColor: '#EDF2F7' },
  severityText: { fontWeight: 'bold', fontSize: 13, color: '#4A5568' },
  submitButton: { backgroundColor: '#3182CE', height: 56, borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  submitButtonText: { color: '#FFFFFF', fontSize: 18, fontWeight: 'bold' },
  warningCard: { backgroundColor: '#FFF5F5', borderLeftWidth: 4, borderLeftColor: '#E53E3E', padding: 16, flexDirection: 'row', alignItems: 'center' },
  warningText: { flex: 1, marginLeft: 12, color: '#9B2C2C', fontSize: 14, fontWeight: '500' },
});
