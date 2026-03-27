import { View, Text, StyleSheet, Image, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function HomeScreen() {
  const features = [
    { id: '1', title: 'Alerte Instantanée', desc: 'Déclenchement SOS en moins de 2s', icon: 'flash', color: '#E53E3E', bg: '#FFF5F5' },
    { id: '2', title: 'Assistance IA', desc: 'Chatbot intelligent 24/7', icon: 'hardware-chip', color: '#3182CE', bg: '#EBF8FF' },
    { id: '3', title: 'Support Légal', desc: 'Assistance et conseils', icon: 'shield-checkmark', color: '#38A169', bg: '#E6FFFA' },
    { id: '4', title: 'Mode Discret', desc: 'Camouflage et discrétion', icon: 'eye-off', color: '#805AD5', bg: '#FAF5FF' },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <View style={styles.headerArea}>
        <Image 
          source={require('../../assets/images/Logo de BOMOKO avec slogan.png')} 
          style={styles.logo} 
          resizeMode="contain"
        />
        <Image 
          source={require('../../assets/images/two-little-sister-girls-hugged-600nw-2253113589.webp')} 
          style={styles.heroImage} 
        />
        <Text style={styles.subtitle}>Votre bouclier de protection et de solidarité.</Text>
      </View>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Votre niveau de risque</Text>
        <Text style={styles.cardContent}>Faible - Tout est normal</Text>
      </View>
      
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Prochain rendez-vous</Text>
        <Text style={styles.cardContent}>Aucun rendez-vous prévu</Text>
      </View>

      <Text style={styles.sectionTitle}>Ce que nous offrons</Text>
      <View style={styles.featuresGrid}>
        {features.map((item) => (
          <View key={item.id} style={styles.featureCard}>
            <View style={[styles.featureIconBox, { backgroundColor: item.bg }]}>
              <Ionicons name={item.icon as any} size={28} color={item.color} />
            </View>
            <Text style={styles.featureTitle}>{item.title}</Text>
            <Text style={styles.featureDesc}>{item.desc}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7FAFC',
  },
  headerArea: {
    padding: 24,
    backgroundColor: '#FFFFFF',
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    marginBottom: 20,
    alignItems: 'center',
    shadowColor: '#1877F2',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 4,
  },
  logo: {
    width: 200,
    height: 80,
    marginBottom: 10,
  },
  heroImage: {
    width: '100%',
    height: 160,
    borderRadius: 16,
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2D3748',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#718096',
    textAlign: 'center',
    fontWeight: '500',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    marginHorizontal: 20,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#4A5568',
    marginBottom: 8,
  },
  cardContent: {
    fontSize: 16,
    color: '#2D3748',
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#2D3748',
    marginHorizontal: 20,
    marginTop: 10,
    marginBottom: 16,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    justifyContent: 'space-between',
  },
  featureCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
    elevation: 2,
  },
  featureIconBox: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  featureTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2D3748',
    textAlign: 'center',
    marginBottom: 6,
  },
  featureDesc: {
    fontSize: 12,
    color: '#718096',
    textAlign: 'center',
    lineHeight: 18,
  }
});
