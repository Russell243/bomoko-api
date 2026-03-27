import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, Alert, ActivityIndicator, FlatList, RefreshControl } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import api from '../../utils/api';

interface Post {
  id: string;
  author_name: string;
  title: string;
  content: string;
  likes_count: number;
  replies_count: number;
  created_at: string;
}

export default function ForumService() {
  const router = useRouter();
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showCompose, setShowCompose] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');
  const [posting, setPosting] = useState(false);

  const fetchPosts = useCallback(async () => {
    try {
      const response = await api.get('/forum/posts/');
      setPosts(response.data.results || response.data || []);
    } catch (error) {
      console.error('Error fetching posts:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);

  const onRefresh = () => { setRefreshing(true); fetchPosts(); };

  const handlePost = async () => {
    if (!newContent.trim()) {
      Alert.alert('Erreur', 'Écrivez quelque chose.');
      return;
    }
    setPosting(true);
    try {
      await api.post('/forum/posts/', {
        title: newTitle || 'Discussion',
        content: newContent,
        is_anonymous: true,
      });
      setNewTitle('');
      setNewContent('');
      setShowCompose(false);
      fetchPosts();
      Alert.alert('Publié ✅', 'Votre message a été partagé avec la communauté.');
    } catch (error: any) {
      Alert.alert('Erreur', 'Impossible de publier. Vérifiez votre connexion.');
    } finally {
      setPosting(false);
    }
  };

  const handleLike = async (postId: string) => {
    try {
      const response = await api.post(`/forum/posts/${postId}/like/`);
      setPosts(prev => prev.map(p => p.id === postId ? { ...p, likes_count: response.data.likes_count } : p));
    } catch { /* ignore */ }
  };

  const timeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `Il y a ${mins}min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `Il y a ${hours}h`;
    return `Il y a ${Math.floor(hours / 24)}j`;
  };

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color="#2D3748" />
        </TouchableOpacity>
        <Text style={styles.title}>Communauté Bomoko</Text>
        <TouchableOpacity onPress={() => setShowCompose(!showCompose)}>
          <Ionicons name={showCompose ? 'close' : 'add-circle'} size={28} color="#805AD5" />
        </TouchableOpacity>
      </View>

      {showCompose && (
        <View style={styles.composeBox}>
          <TextInput style={styles.composeTitle} placeholder="Titre (optionnel)" value={newTitle} onChangeText={setNewTitle} />
          <TextInput style={styles.composeInput} placeholder="Partagez quelque chose avec la communauté..." multiline numberOfLines={3} value={newContent} onChangeText={setNewContent} />
          <TouchableOpacity style={styles.publishBtn} onPress={handlePost} disabled={posting}>
            {posting ? <ActivityIndicator color="#FFF" /> : <Text style={styles.publishText}>Publier anonymement</Text>}
          </TouchableOpacity>
        </View>
      )}

      {loading ? (
        <ActivityIndicator size="large" color="#805AD5" style={{ marginTop: 60 }} />
      ) : posts.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="chatbubbles-outline" size={48} color="#A0AEC0" />
          <Text style={styles.emptyText}>Aucune discussion encore.{'\n'}Soyez le premier à partager !</Text>
        </View>
      ) : (
        <FlatList
          data={posts}
          keyExtractor={item => item.id}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
          contentContainerStyle={{ padding: 16 }}
          renderItem={({ item }) => (
            <View style={styles.postCard}>
              <View style={styles.postHeader}>
                <View style={styles.avatarMini} />
                <View>
                  <Text style={styles.userName}>{item.author_name}</Text>
                  <Text style={styles.time}>{timeAgo(item.created_at)}</Text>
                </View>
              </View>
              {item.title !== 'Discussion' && <Text style={styles.postTitle}>{item.title}</Text>}
              <Text style={styles.content}>{item.content}</Text>
              <View style={styles.postFooter}>
                <TouchableOpacity style={styles.stat} onPress={() => handleLike(item.id)}>
                  <Ionicons name="heart-outline" size={20} color="#E53E3E" />
                  <Text style={styles.statText}>{item.likes_count}</Text>
                </TouchableOpacity>
                <View style={styles.stat}>
                  <Ionicons name="chatbubble-outline" size={20} color="#718096" />
                  <Text style={styles.statText}>{item.replies_count}</Text>
                </View>
              </View>
            </View>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F7FAFC' },
  topBar: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingTop: 50, paddingBottom: 16, backgroundColor: '#FFF', borderBottomWidth: 1, borderBottomColor: '#EDF2F7' },
  title: { fontSize: 20, fontWeight: '900', color: '#2D3748' },
  composeBox: { margin: 16, backgroundColor: '#FFF', borderRadius: 16, padding: 16, elevation: 2, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5 },
  composeTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 8, color: '#2D3748' },
  composeInput: { fontSize: 15, color: '#4A5568', minHeight: 60, textAlignVertical: 'top' },
  publishBtn: { backgroundColor: '#805AD5', borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 12 },
  publishText: { color: '#FFF', fontWeight: 'bold', fontSize: 15 },
  emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingTop: 100 },
  emptyText: { color: '#A0AEC0', fontSize: 16, textAlign: 'center', marginTop: 16 },
  postCard: { backgroundColor: '#FFFFFF', borderRadius: 16, padding: 20, marginBottom: 16, elevation: 2, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5 },
  postHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  avatarMini: { width: 32, height: 32, borderRadius: 16, backgroundColor: '#805AD5', marginRight: 10, opacity: 0.5 },
  userName: { fontSize: 14, fontWeight: 'bold', color: '#2D3748' },
  time: { fontSize: 12, color: '#A0AEC0' },
  postTitle: { fontSize: 16, fontWeight: 'bold', color: '#2D3748', marginBottom: 4 },
  content: { fontSize: 15, lineHeight: 22, color: '#4A5568', marginBottom: 16 },
  postFooter: { flexDirection: 'row', borderTopWidth: 1, borderTopColor: '#F7FAFC', paddingTop: 12 },
  stat: { flexDirection: 'row', alignItems: 'center', marginRight: 24 },
  statText: { marginLeft: 6, color: '#718096', fontSize: 14 },
});
