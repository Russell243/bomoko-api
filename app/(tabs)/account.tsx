import { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { router } from 'expo-router';
import api, { clearAllTokens, getApiOrigin } from '../../utils/api';

type ProfileResponse = {
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  role: string;
};

export default function AccountScreen() {
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<ProfileResponse>({
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    role: '',
  });
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await api.get('/users/profile/');
        setProfile({
          username: response.data.username || '',
          first_name: response.data.first_name || '',
          last_name: response.data.last_name || '',
          email: response.data.email || '',
          phone_number: response.data.phone_number || '',
          role: response.data.profile?.role || '',
        });
      } catch {
        // handled by global 401 interceptor
      }
    };
    loadProfile();
  }, []);

  const saveProfile = async () => {
    const normalizedProfile = {
      ...profile,
      username: profile.username.trim(),
      first_name: profile.first_name.trim(),
      last_name: profile.last_name.trim(),
      email: profile.email.trim(),
    };
    if (!normalizedProfile.username) {
      Alert.alert('Erreur', "Le nom d'utilisateur est requis.");
      return;
    }

    setLoading(true);
    try {
      await api.put('/users/profile/', normalizedProfile);
      setProfile(normalizedProfile);
      Alert.alert('Succes', 'Profil mis a jour.');
    } catch (error: any) {
      Alert.alert('Erreur', error?.response?.data?.detail || 'Impossible de mettre a jour le profil.');
    } finally {
      setLoading(false);
    }
  };

  const changePassword = async () => {
    if (!currentPassword || !newPassword) {
      Alert.alert('Erreur', 'Saisissez le mot de passe actuel et le nouveau.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/change-password/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword('');
      setNewPassword('');
      Alert.alert('Succes', 'Mot de passe modifie.');
    } catch (error: any) {
      Alert.alert('Erreur', error?.response?.data?.detail || 'Impossible de changer le mot de passe.');
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    await clearAllTokens();
    router.replace('/(auth)/welcome');
  };

  const suspendAccount = async () => {
    Alert.alert('Suspendre le compte', 'Voulez-vous vraiment suspendre votre compte ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Suspendre',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.post('/users/deactivate/', {});
            await logout();
          } catch (error: any) {
            Alert.alert('Erreur', error?.response?.data?.detail || 'Impossible de suspendre le compte.');
          }
        },
      },
    ]);
  };

  const deleteAccount = async () => {
    Alert.alert('Supprimer le compte', 'Cette action est irreversible. Continuer ?', [
      { text: 'Annuler', style: 'cancel' },
      {
        text: 'Supprimer',
        style: 'destructive',
        onPress: async () => {
          try {
            await api.post('/users/delete/', {});
            await logout();
          } catch (error: any) {
            Alert.alert('Erreur', error?.response?.data?.detail || 'Impossible de supprimer le compte.');
          }
        },
      },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Mon Compte</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Profil</Text>
        <TextInput style={styles.input} value={profile.username} onChangeText={(v) => setProfile({ ...profile, username: v })} placeholder="Nom d'utilisateur" />
        <TextInput style={styles.input} value={profile.first_name} onChangeText={(v) => setProfile({ ...profile, first_name: v })} placeholder="Prenom" />
        <TextInput style={styles.input} value={profile.last_name} onChangeText={(v) => setProfile({ ...profile, last_name: v })} placeholder="Nom" />
        <TextInput style={styles.input} value={profile.email} onChangeText={(v) => setProfile({ ...profile, email: v })} placeholder="Email" />
        <TextInput style={[styles.input, styles.inputDisabled]} value={profile.phone_number} editable={false} placeholder="Telephone" />
        <TouchableOpacity style={styles.primaryButton} disabled={loading} onPress={saveProfile}>
          <Text style={styles.primaryButtonText}>Enregistrer</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Securite</Text>
        <TextInput style={styles.input} value={currentPassword} onChangeText={setCurrentPassword} placeholder="Mot de passe actuel" secureTextEntry />
        <TextInput style={styles.input} value={newPassword} onChangeText={setNewPassword} placeholder="Nouveau mot de passe" secureTextEntry />
        <TouchableOpacity style={styles.primaryButton} disabled={loading} onPress={changePassword}>
          <Text style={styles.primaryButtonText}>Changer le mot de passe</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Session et compte</Text>
        {profile.role === 'admin' && (
          <TouchableOpacity 
            style={styles.adminButton} 
            onPress={() => {
              const adminUrl = `${getApiOrigin()}/admin/`;
              import('react-native').then(rn => rn.Linking.openURL(adminUrl));
            }}
          >
            <Text style={styles.adminButtonText}>🛠️ Tableau de Bord Admin</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity style={styles.secondaryButton} onPress={logout}>
          <Text style={styles.secondaryButtonText}>Se deconnecter</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.warningButton} onPress={suspendAccount}>
          <Text style={styles.warningButtonText}>Suspendre le compte</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.dangerButton} onPress={deleteAccount}>
          <Text style={styles.dangerButtonText}>Supprimer le compte</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F0F2F5' },
  content: { padding: 16, paddingBottom: 40 },
  title: { fontSize: 28, fontWeight: '900', color: '#1C1E21', marginBottom: 12 },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E4E6EB',
  },
  cardTitle: { fontSize: 16, fontWeight: '800', color: '#1C1E21', marginBottom: 10 },
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: '#CCD0D5',
    borderRadius: 8,
    paddingHorizontal: 12,
    marginBottom: 10,
    backgroundColor: '#FFFFFF',
  },
  inputDisabled: { backgroundColor: '#F0F2F5' },
  primaryButton: { backgroundColor: '#1877F2', paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  primaryButtonText: { color: '#FFFFFF', fontWeight: '800' },
  secondaryButton: {
    backgroundColor: '#E7F3FF',
    borderColor: '#1877F2',
    borderWidth: 1,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8,
  },
  secondaryButtonText: { color: '#1877F2', fontWeight: '800' },
  warningButton: { backgroundColor: '#FFF4E5', paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
  warningButtonText: { color: '#AD6800', fontWeight: '800' },
  dangerButton: { backgroundColor: '#FFEBEE', paddingVertical: 12, borderRadius: 8, alignItems: 'center' },
  dangerButtonText: { color: '#C62828', fontWeight: '800' },
  adminButton: { backgroundColor: '#2D3748', paddingVertical: 12, borderRadius: 8, alignItems: 'center', marginBottom: 8 },
  adminButtonText: { color: '#E2E8F0', fontWeight: '800' },
});
