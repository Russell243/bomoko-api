import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, ActivityIndicator, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';

export default function LegalService() {
  const router = useRouter();
  const [selectedType, setSelectedType] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isUrgent, setIsUrgent] = useState(false);
  const [loading, setLoading] = useState(false);

  const caseTypes = [
    { key: 'complaint', label: 'Porter Plainte', icon: 'document-text-outline' },
    { key: 'consultation', label: 'Conseil Immédiat', icon: 'chatbubbles-outline' },
    { key: 'protection_order', label: 'Ordonnance de Protection', icon: 'shield-checkmark-outline' },
    { key: 'custody', label: 'Garde d\'enfants', icon: 'people-outline' },
  ];

  const submitCase = async () => {
    if (!selectedType || !description.trim()) {
      Alert.alert('Erreur', 'Veuillez choisir un type et décrire votre situation.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/legal/cases/', {
        case_type: selectedType,
        title: title || `Demande ${caseTypes.find(c => c.key === selectedType)?.label}`,
        description,
        is_urgent: isUrgent,
        is_anonymous: true,
      });
      Alert.alert(
        "Demande envoyée ✅",
        "Votre dossier a été transmis. Un conseiller juridique vous contactera sous 24h.",
        [{ text: "OK", onPress: () => router.back() }]
      );
    } catch (error: any) {
      const msg = error.response?.status === 401
        ? 'Connectez-vous pour soumettre une demande.'
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
          source={require('../../assets/images/statue-justice-on-lawyers-desk-600nw-2589689745.webp')} 
          style={styles.heroImage} 
        />
        <View style={styles.iconCircle}>
          <Ionicons name="shield-checkmark" size={40} color="#38A169" />
        </View>
        <Text style={styles.title}>Support Juridique</Text>
        <Text style={styles.subtitle}>Conseil anonyme et assistance pour vos démarches légales.</Text>
      </View>

      <Text style={styles.label}>Type de demande</Text>
      <View style={styles.optionsContainer}>
        {caseTypes.map(ct => (
          <TouchableOpacity
            key={ct.key}
            style={[styles.optionCard, selectedType === ct.key && styles.optionCardSelected]}
            onPress={() => setSelectedType(ct.key)}
          >
            <View style={styles.optionHeader}>
              <Ionicons name={ct.icon as any} size={24} color={selectedType === ct.key ? '#FFF' : '#38A169'} />
              <Text style={[styles.optionTitle, selectedType === ct.key && { color: '#FFF' }]}>{ct.label}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.label}>Titre (optionnel)</Text>
      <TextInput
        style={styles.input}
        placeholder="Ex: Menaces par un voisin"
        value={title}
        onChangeText={setTitle}
      />

      <Text style={styles.label}>Décrivez votre situation</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Expliquez les faits en détail..."
        multiline
        numberOfLines={5}
        value={description}
        onChangeText={setDescription}
      />

      <TouchableOpacity style={styles.urgentToggle} onPress={() => setIsUrgent(!isUrgent)}>
        <Ionicons name={isUrgent ? 'checkbox' : 'square-outline'} size={24} color="#E53E3E" />
        <Text style={styles.urgentText}>⚡ C'est urgent (réponse prioritaire)</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.submitButton} onPress={submitCase} disabled={loading}>
        {loading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.submitButtonText}>Soumettre la demande</Text>}
      </TouchableOpacity>

      <View style={styles.secretCard}>
        <Text style={styles.secretText}>🔒 Confidentialité Totale : Vos échanges sont chiffrés et anonymisés par défaut.</Text>
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
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#E6FFFA', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 24, fontWeight: '900', color: '#2D3748', textAlign: 'center' },
  subtitle: { fontSize: 15, color: '#718096', textAlign: 'center', marginTop: 8, lineHeight: 22 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#4A5568', marginBottom: 8, marginTop: 16 },
  optionsContainer: { marginBottom: 16 },
  optionCard: { backgroundColor: '#F7FAFC', borderRadius: 16, padding: 16, marginBottom: 10, borderWidth: 1, borderColor: '#E2E8F0' },
  optionCardSelected: { backgroundColor: '#38A169', borderColor: '#38A169' },
  optionHeader: { flexDirection: 'row', alignItems: 'center' },
  optionTitle: { fontSize: 16, fontWeight: 'bold', color: '#2D3748', marginLeft: 12 },
  input: { backgroundColor: '#F7FAFC', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: '#E2E8F0', fontSize: 16 },
  textArea: { height: 120, textAlignVertical: 'top' },
  urgentToggle: { flexDirection: 'row', alignItems: 'center', marginTop: 20, marginBottom: 24 },
  urgentText: { marginLeft: 10, fontSize: 15, fontWeight: '600', color: '#E53E3E' },
  submitButton: { backgroundColor: '#38A169', height: 56, borderRadius: 12, justifyContent: 'center', alignItems: 'center' },
  submitButtonText: { color: '#FFFFFF', fontSize: 18, fontWeight: 'bold' },
  secretCard: { backgroundColor: '#EDF2F7', padding: 16, borderRadius: 12, alignItems: 'center', marginTop: 32 },
  secretText: { fontSize: 13, color: '#4A5568', fontWeight: '600', textAlign: 'center' },
});
