import { useEffect, useState } from 'react';
import { Alert, FlatList, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import api from '../../utils/api';

type Contact = {
  id: string;
  name: string;
  phone_number: string;
  relationship?: string;
};

const MIN_CONTACTS_REQUIRED = 3;

export default function SosContactsScreen() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [relationship, setRelationship] = useState('');

  const loadContacts = async () => {
    setLoading(true);
    try {
      const response = await api.get('/sos/contacts/');
      const payload = response.data;
      const list = Array.isArray(payload) ? payload : payload?.results ?? [];
      setContacts(list);
    } catch {
      Alert.alert('Erreur', 'Impossible de charger les contacts.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadContacts();
  }, []);

  const resetForm = () => {
    setEditingId(null);
    setName('');
    setPhoneNumber('');
    setRelationship('');
  };

  const saveContact = async () => {
    if (!name.trim() || !phoneNumber.trim()) {
      Alert.alert('Erreur', 'Nom et numero sont obligatoires.');
      return;
    }

    try {
      if (editingId) {
        await api.patch(`/sos/contacts/${editingId}/`, {
          name,
          phone_number: phoneNumber,
          relationship,
        });
      } else {
        await api.post('/sos/contacts/', {
          name,
          phone_number: phoneNumber,
          relationship,
        });
      }
      resetForm();
      await loadContacts();
    } catch {
      Alert.alert('Erreur', "Impossible d'enregistrer le contact.");
    }
  };

  const startEdit = (contact: Contact) => {
    setEditingId(contact.id);
    setName(contact.name);
    setPhoneNumber(contact.phone_number);
    setRelationship(contact.relationship || '');
  };

  const removeContact = async (id: string) => {
    Alert.alert('Supprimer', 'Supprimer ce contact de confiance ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Supprimer',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.delete(`/sos/contacts/${id}/`);
            await loadContacts();
          } catch {
            Alert.alert('Erreur', 'Suppression impossible.');
          }
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Contacts de confiance</Text>
      <Text style={styles.subtitle}>
        Minimum requis pour activer SOS: {MIN_CONTACTS_REQUIRED}. Actuel: {contacts.length}
      </Text>

      <View style={styles.formCard}>
        <TextInput style={styles.input} placeholder="Nom" value={name} onChangeText={setName} />
        <TextInput
          style={styles.input}
          placeholder="+243..."
          keyboardType="phone-pad"
          value={phoneNumber}
          onChangeText={setPhoneNumber}
        />
        <TextInput
          style={styles.input}
          placeholder="Relation (optionnel)"
          value={relationship}
          onChangeText={setRelationship}
        />
        <View style={styles.formActions}>
          <TouchableOpacity style={styles.primaryButton} onPress={saveContact}>
            <Text style={styles.primaryButtonText}>{editingId ? 'Mettre a jour' : 'Ajouter'}</Text>
          </TouchableOpacity>
          {editingId && (
            <TouchableOpacity style={styles.secondaryButton} onPress={resetForm}>
              <Text style={styles.secondaryButtonText}>Annuler</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      <FlatList
        data={contacts}
        keyExtractor={(item) => item.id}
        refreshing={loading}
        onRefresh={loadContacts}
        renderItem={({ item }) => (
          <View style={styles.contactRow}>
            <View style={styles.contactTextCol}>
              <Text style={styles.contactName}>{item.name}</Text>
              <Text style={styles.contactPhone}>{item.phone_number}</Text>
              {!!item.relationship && <Text style={styles.contactRelation}>{item.relationship}</Text>}
            </View>
            <View style={styles.contactActions}>
              <TouchableOpacity style={styles.actionBtn} onPress={() => startEdit(item)}>
                <Text style={styles.actionEdit}>Modifier</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.actionBtn} onPress={() => removeContact(item.id)}>
                <Text style={styles.actionDelete}>Supprimer</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>Aucun contact enregistre.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F8FAFC', padding: 16 },
  title: { fontSize: 24, fontWeight: '900', color: '#0F172A' },
  subtitle: { color: '#475569', marginTop: 6, marginBottom: 14 },
  formCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    marginBottom: 12,
  },
  input: {
    height: 44,
    borderColor: '#CBD5E1',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 8,
    backgroundColor: '#FFFFFF',
  },
  formActions: { flexDirection: 'row', gap: 8 },
  primaryButton: { backgroundColor: '#1877F2', borderRadius: 8, paddingVertical: 10, paddingHorizontal: 14 },
  primaryButtonText: { color: '#FFFFFF', fontWeight: '800' },
  secondaryButton: { backgroundColor: '#E2E8F0', borderRadius: 8, paddingVertical: 10, paddingHorizontal: 14 },
  secondaryButtonText: { color: '#1E293B', fontWeight: '700' },
  contactRow: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    padding: 12,
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  contactTextCol: { flex: 1, marginRight: 8 },
  contactName: { fontWeight: '800', color: '#0F172A' },
  contactPhone: { color: '#334155', marginTop: 2 },
  contactRelation: { color: '#64748B', marginTop: 2 },
  contactActions: { justifyContent: 'center', gap: 6 },
  actionBtn: { paddingVertical: 4 },
  actionEdit: { color: '#0369A1', fontWeight: '700' },
  actionDelete: { color: '#B91C1C', fontWeight: '700' },
  emptyText: { textAlign: 'center', color: '#64748B', marginTop: 20 },
});
