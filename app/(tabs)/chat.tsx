import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import api, { getAuthToken } from '../../utils/api';

interface Message {
  id: string;
  content: string;
  is_user: boolean;
}

export default function ChatScreen() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceLoading, setIsVoiceLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);

  useEffect(() => {
    const initChat = async () => {
      const token = await getAuthToken();
      if (!token) return;

      try {
        const response = await api.get('/chat/conversations/');
        if (response.data.results && response.data.results.length > 0) {
          const conv = response.data.results[0];
          setConversationId(conv.id);
          const msgResponse = await api.get(`/chat/conversations/${conv.id}/`);
          setMessages(
            msgResponse.data.messages.map((m: any) => ({
              id: m.id.toString(),
              content: m.content,
              is_user: m.is_user,
            }))
          );
        } else {
          const newConv = await api.post('/chat/conversations/', { title: 'Discussion Bomoko' });
          setConversationId(newConv.data.id);
          setMessages([
            {
              id: 'welcome',
              content: "Bonjour, je suis votre assistant Bomoko. Comment puis-je vous aider aujourd'hui ?",
              is_user: false,
            },
          ]);
        }
      } catch {
        Alert.alert('Erreur', "Impossible d'initialiser la conversation.");
      }
    };
    initChat();
  }, []);

  const maybeShowDangerPrompt = (dangerDetected: boolean) => {
    if (!dangerDetected) return;
    Alert.alert(
      'DANGER DETECTE',
      "L'IA a detecte une situation de danger. Souhaitez-vous declencher l'alerte SOS ?",
      [
        { text: 'Non', style: 'cancel' },
        { text: 'OUI, SOS', style: 'destructive', onPress: () => router.push('/(tabs)/sos') },
      ]
    );
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !conversationId) return;

    const userText = inputText;
    setInputText('');

    const tempUserMsg: Message = {
      id: Date.now().toString(),
      content: userText,
      is_user: true,
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await api.post(`/chat/conversations/${conversationId}/send_message/`, {
        content: userText,
      });

      const aiMsg: Message = {
        id: response.data.ai_response.id.toString(),
        content: response.data.ai_response.content,
        is_user: false,
      };

      setMessages((prev) => [...prev, aiMsg]);
      maybeShowDangerPrompt(response.data.danger_detected);
    } catch (error) {
      Alert.alert('Erreur', "Impossible d'envoyer le message. Verifiez votre connexion.");
    } finally {
      setIsLoading(false);
    }
  };

  const sendVoiceMessage = async () => {
    if (!conversationId) return;

    if (Platform.OS !== 'web' || typeof document === 'undefined') {
      Alert.alert('Info', 'Envoi vocal natif a finaliser. Utilisez la version web pour le moment.');
      return;
    }

    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'audio/*';
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;

      setIsVoiceLoading(true);
      try {
        const formData = new FormData();
        formData.append('audio', file);

        const response = await api.post(
          `/chat/conversations/${conversationId}/voice/`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );

        const userVoiceMsg: Message = {
          id: `${Date.now()}-voice`,
          content: `[Vocal] ${response.data.transcription}`,
          is_user: true,
        };
        const aiMsg: Message = {
          id: response.data.ai_response.id.toString(),
          content: response.data.ai_response.content,
          is_user: false,
        };
        setMessages((prev) => [...prev, userVoiceMsg, aiMsg]);
        maybeShowDangerPrompt(response.data.danger_detected);
      } catch (error: any) {
        Alert.alert('Erreur', error?.response?.data?.detail || "Impossible d'envoyer l'audio.");
      } finally {
        setIsVoiceLoading(false);
      }
    };
    input.click();
  };

  const renderMessage = ({ item }: { item: Message }) => {
    const isUser = item.is_user;

    return (
      <View style={[styles.bubbleWrapper, isUser ? styles.bubbleWrapperUser : styles.bubbleWrapperAI]}>
        {!isUser && (
          <View style={styles.aiAvatar}>
            <Text style={styles.avatarText}>B</Text>
          </View>
        )}
        <View style={[styles.bubble, isUser ? styles.userBubble : styles.aiBubble]}>
          <Text style={[styles.messageText, isUser ? styles.userMessageText : styles.aiMessageText]}>
            {item.content}
          </Text>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={90}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Assistant IA Bomoko</Text>
        <Text style={styles.headerSubtitle}>Confidentiel et securise</Text>
      </View>

      <FlatList
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContainer}
        showsVerticalScrollIndicator={false}
      />

      {(isLoading || isVoiceLoading) && (
        <Text style={styles.loadingText}>
          {isVoiceLoading ? 'Traitement du message vocal...' : 'Bomoko ecrit un message...'}
        </Text>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Tapez votre message ici..."
          placeholderTextColor="#A0AEC0"
        />
        <TouchableOpacity style={styles.voiceButton} onPress={sendVoiceMessage}>
          <Text style={styles.voiceButtonText}>Vocal</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
          <Text style={styles.sendButtonText}>Envoyer</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7FAFC',
  },
  header: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E2E8F0',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#2D3748',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#718096',
    marginTop: 2,
  },
  listContainer: {
    padding: 16,
    paddingBottom: 20,
  },
  bubbleWrapper: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  bubbleWrapperUser: {
    justifyContent: 'flex-end',
  },
  bubbleWrapperAI: {
    justifyContent: 'flex-start',
  },
  aiAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#1877F2',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 8,
  },
  avatarText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  bubble: {
    maxWidth: '75%',
    padding: 14,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: '#1877F2',
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: '#EDF2F7',
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: '#FFFFFF',
  },
  aiMessageText: {
    color: '#2D3748',
  },
  loadingText: {
    paddingHorizontal: 20,
    paddingBottom: 10,
    fontSize: 12,
    color: '#A0AEC0',
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E2E8F0',
    alignItems: 'center',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#F7FAFC',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    color: '#2D3748',
  },
  voiceButton: {
    marginLeft: 8,
    backgroundColor: '#E7F3FF',
    borderWidth: 1,
    borderColor: '#1877F2',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
  },
  voiceButtonText: {
    color: '#1877F2',
    fontWeight: 'bold',
    fontSize: 14,
  },
  sendButton: {
    marginLeft: 8,
    backgroundColor: '#1877F2',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
});
