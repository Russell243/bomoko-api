import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, ActivityIndicator, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';

interface HealthMetric {
  id: string;
  metric_type: string;
  value: number;
  notes: string;
  recorded_at: string;
}

const METRIC_LABELS: { [key: string]: string } = {
  weight: 'Poids (kg)',
  blood_pressure_sys: 'Pression (sys)',
  blood_pressure_dia: 'Pression (dia)',
  heart_rate: 'Fréq. cardiaque',
  temperature: 'Temp. (°C)',
  sleep_hours: 'Heures de sommeil',
  pain_level: 'Niveau douleur',
  mood: 'Humeur (1-10)',
};

export default function HealthService() {
  const router = useRouter();
  const [metrics, setMetrics] = useState<HealthMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [selectedType, setSelectedType] = useState('mood');
  const [value, setValue] = useState('');
  const [notes, setNotes] = useState('');
  const [posting, setPosting] = useState(false);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await api.get('/health/vitals/');
      setMetrics(response.data.results || response.data || []);
    } catch (error) {
      console.error('Error fetching vitals:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchMetrics(); }, [fetchMetrics]);

  const onRefresh = () => { setRefreshing(true); fetchMetrics(); };

  const submitMetric = async () => {
    if (!value.trim() || isNaN(Number(value))) {
      Alert.alert('Erreur', 'Entrez une valeur numérique.');
      return;
    }
    setPosting(true);
    try {
      await api.post('/health/vitals/', {
        metric_type: selectedType,
        value: parseFloat(value),
        notes,
      });
      setValue('');
      setNotes('');
      setShowAdd(false);
      fetchMetrics();
      Alert.alert('Enregistré ✅', 'Vos données de santé ont été sauvegardées.');
    } catch (error: any) {
      Alert.alert('Erreur', 'Impossible d\'enregistrer. Vérifiez votre connexion.');
    } finally {
      setPosting(false);
    }
  };

  // Get latest value for a given metric type
  const getLatest = (type: string) => {
    const m = metrics.find(m => m.metric_type === type);
    return m ? String(m.value) : '--';
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
        <Ionicons name="arrow-back" size={24} color="#2D3748" />
      </TouchableOpacity>

      <View style={styles.header}>
        <View style={styles.iconCircle}>
          <Ionicons name="heart" size={40} color="#E53E3E" />
        </View>
        <Text style={styles.title}>Suivi Santé</Text>
        <Text style={styles.subtitle}>Suivez vos constantes vitales et votre bien-être.</Text>
      </View>

      {/* Quick stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{getLatest('mood')}</Text>
          <Text style={styles.statLabel}>Humeur</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{getLatest('weight')}</Text>
          <Text style={styles.statLabel}>Poids</Text>
        </View>
        <View style={styles.statBox}>
          <Text style={styles.statValue}>{getLatest('sleep_hours')}</Text>
          <Text style={styles.statLabel}>Sommeil</Text>
        </View>
      </View>

      {/* Add metric button */}
      <TouchableOpacity style={styles.addBtn} onPress={() => setShowAdd(!showAdd)}>
        <Ionicons name={showAdd ? 'close-circle' : 'add-circle'} size={24} color="#FFF" />
        <Text style={styles.addBtnText}>{showAdd ? 'Fermer' : 'Ajouter une mesure'}</Text>
      </TouchableOpacity>

      {showAdd && (
        <View style={styles.addForm}>
          <Text style={styles.label}>Type de mesure</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipScroll}>
            {Object.entries(METRIC_LABELS).map(([key, label]) => (
              <TouchableOpacity
                key={key}
                style={[styles.chip, selectedType === key && styles.chipActive]}
                onPress={() => setSelectedType(key)}
              >
                <Text style={[styles.chipText, selectedType === key && styles.chipTextActive]}>{label}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <Text style={styles.label}>Valeur</Text>
          <TextInput style={styles.input} placeholder="Ex: 72" keyboardType="numeric" value={value} onChangeText={setValue} />

          <Text style={styles.label}>Notes (optionnel)</Text>
          <TextInput style={styles.input} placeholder="Ex: Après le repas..." value={notes} onChangeText={setNotes} />

          <TouchableOpacity style={styles.submitBtn} onPress={submitMetric} disabled={posting}>
            {posting ? <ActivityIndicator color="#FFF" /> : <Text style={styles.submitText}>Enregistrer</Text>}
          </TouchableOpacity>
        </View>
      )}

      {/* Recent entries */}
      <Text style={styles.sectionTitle}>Historique récent</Text>
      {loading ? (
        <ActivityIndicator color="#E53E3E" style={{ marginTop: 20 }} />
      ) : metrics.length === 0 ? (
        <View style={styles.emptyCard}>
          <Ionicons name="pulse-outline" size={32} color="#A0AEC0" />
          <Text style={styles.emptyText}>Aucune donnée enregistrée.{'\n'}Commencez par ajouter une mesure.</Text>
        </View>
      ) : (
        metrics.slice(0, 10).map(m => (
          <View key={m.id} style={styles.entryRow}>
            <View>
              <Text style={styles.entryType}>{METRIC_LABELS[m.metric_type] || m.metric_type}</Text>
              {m.notes ? <Text style={styles.entryNotes}>{m.notes}</Text> : null}
            </View>
            <Text style={styles.entryValue}>{m.value}</Text>
          </View>
        ))
      )}

      <View style={styles.tipCard}>
        <Text style={styles.tipTitle}>💡 Conseil du jour</Text>
        <Text style={styles.tipDesc}>Buvez au moins 2 litres d'eau par jour pour rester bien hydratée et en bonne santé.</Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF' },
  scrollContent: { padding: 24 },
  backButton: { marginTop: 20, marginBottom: 20 },
  header: { alignItems: 'center', marginBottom: 24 },
  iconCircle: { width: 80, height: 80, borderRadius: 40, backgroundColor: '#FFF5F5', justifyContent: 'center', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 24, fontWeight: '900', color: '#2D3748', textAlign: 'center' },
  subtitle: { fontSize: 15, color: '#718096', textAlign: 'center', marginTop: 8 },
  statsContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  statBox: { flex: 1, backgroundColor: '#FFF5F5', padding: 16, borderRadius: 16, alignItems: 'center', marginHorizontal: 4 },
  statValue: { fontSize: 22, fontWeight: '900', color: '#E53E3E' },
  statLabel: { color: '#C53030', fontSize: 12, marginTop: 4, fontWeight: '500' },
  addBtn: { flexDirection: 'row', backgroundColor: '#E53E3E', borderRadius: 12, padding: 14, alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 16 },
  addBtnText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' },
  addForm: { backgroundColor: '#F7FAFC', borderRadius: 16, padding: 20, marginBottom: 24 },
  label: { fontSize: 14, fontWeight: 'bold', color: '#4A5568', marginBottom: 8, marginTop: 12 },
  chipScroll: { flexDirection: 'row', marginBottom: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: 20, backgroundColor: '#EDF2F7', marginRight: 8 },
  chipActive: { backgroundColor: '#E53E3E' },
  chipText: { fontWeight: 'bold', fontSize: 12, color: '#4A5568' },
  chipTextActive: { color: '#FFF' },
  input: { backgroundColor: '#FFF', borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#E2E8F0', fontSize: 16 },
  submitBtn: { backgroundColor: '#E53E3E', borderRadius: 12, padding: 14, alignItems: 'center', marginTop: 16 },
  submitText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#2D3748', marginBottom: 12, marginTop: 8 },
  emptyCard: { alignItems: 'center', padding: 32, backgroundColor: '#F7FAFC', borderRadius: 16, borderWidth: 1, borderStyle: 'dashed', borderColor: '#E2E8F0' },
  emptyText: { marginTop: 12, color: '#718096', fontSize: 15, textAlign: 'center' },
  entryRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#EDF2F7' },
  entryType: { fontSize: 15, fontWeight: '600', color: '#2D3748' },
  entryNotes: { fontSize: 12, color: '#A0AEC0', marginTop: 2 },
  entryValue: { fontSize: 20, fontWeight: '900', color: '#E53E3E' },
  tipCard: { backgroundColor: '#F0FFF4', padding: 20, borderRadius: 16, borderLeftWidth: 4, borderLeftColor: '#48BB78', marginTop: 24 },
  tipTitle: { color: '#2F855A', fontWeight: 'bold', fontSize: 16, marginBottom: 4 },
  tipDesc: { color: '#276749', fontSize: 14, lineHeight: 20 },
});
