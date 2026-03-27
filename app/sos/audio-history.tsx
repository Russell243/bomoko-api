import { useEffect, useState } from 'react';
import { Alert, FlatList, Platform, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import api from '../../utils/api';

type AudioHistoryItem = {
  alert_id: string;
  created_at: string;
  resolved_at: string | null;
  audio_original_name: string;
  audio_mime_type: string;
  audio_encrypted: boolean;
};

export default function SosAudioHistoryScreen() {
  const [items, setItems] = useState<AudioHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const response = await api.get('/sos/alerts/audio-history/');
      setItems(response.data || []);
    } catch {
      Alert.alert('Erreur', "Impossible de charger l'historique audio.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const playAudio = async (item: AudioHistoryItem) => {
    try {
      const response = await api.get(`/sos/alerts/${item.alert_id}/audio-stream/`, {
        responseType: 'arraybuffer',
      });

      if (Platform.OS === 'web' && typeof window !== 'undefined') {
        const blob = new Blob([response.data], { type: item.audio_mime_type || 'audio/mpeg' });
        const url = URL.createObjectURL(blob);
        const player = new Audio(url);
        player.onended = () => URL.revokeObjectURL(url);
        await player.play();
        return;
      }

      Alert.alert('Info', 'Lecture audio integree disponible sur web. Sur mobile, on peut ajouter un player natif ensuite.');
    } catch {
      Alert.alert('Erreur', "Impossible d'ecouter cet enregistrement.");
    }
  };

  const deleteAudio = (alertId: string) => {
    Alert.alert('Supprimer', 'Supprimer cet audio enregistre ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Supprimer',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.delete(`/sos/alerts/${alertId}/audio/`);
            await loadHistory();
          } catch {
            Alert.alert('Erreur', 'Suppression impossible.');
          }
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Historique audio SOS</Text>
      <Text style={styles.subtitle}>Acces prive de votre session. Audio chiffre: {items.some((it) => it.audio_encrypted) ? 'Oui' : 'N/A'}</Text>

      <FlatList
        data={items}
        keyExtractor={(item) => item.alert_id}
        refreshing={loading}
        onRefresh={loadHistory}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.name}>{item.audio_original_name || 'audio-record'}</Text>
            <Text style={styles.meta}>Alerte: {item.alert_id}</Text>
            <Text style={styles.meta}>
              Date: {new Date(item.created_at).toLocaleString()}
            </Text>
            <Text style={styles.meta}>Chiffre: {item.audio_encrypted ? 'Oui' : 'Non'}</Text>

            <View style={styles.actionsRow}>
              <TouchableOpacity style={styles.playBtn} onPress={() => playAudio(item)}>
                <Text style={styles.playText}>Ecouter</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.keepBtn} onPress={() => Alert.alert('Conserve', 'Cet audio est conserve.')}>
                <Text style={styles.keepText}>Conserver</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.deleteBtn} onPress={() => deleteAudio(item.alert_id)}>
                <Text style={styles.deleteText}>Supprimer</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>Aucun enregistrement audio pour le moment.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC', padding: 16 },
  title: { fontSize: 24, fontWeight: '900', color: '#0F172A' },
  subtitle: { color: '#475569', marginTop: 6, marginBottom: 12 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    marginBottom: 10,
  },
  name: { fontWeight: '800', color: '#0F172A' },
  meta: { color: '#475569', marginTop: 2, fontSize: 12 },
  actionsRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  playBtn: { backgroundColor: '#DBEAFE', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10 },
  playText: { color: '#1D4ED8', fontWeight: '700' },
  keepBtn: { backgroundColor: '#DCFCE7', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10 },
  keepText: { color: '#166534', fontWeight: '700' },
  deleteBtn: { backgroundColor: '#FEE2E2', borderRadius: 8, paddingVertical: 8, paddingHorizontal: 10 },
  deleteText: { color: '#B91C1C', fontWeight: '700' },
  emptyText: { textAlign: 'center', color: '#64748B', marginTop: 20 },
});
