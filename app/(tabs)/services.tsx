import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

export default function ServicesScreen() {
  const router = useRouter();

  const services = [
    { 
      id: 'medical', 
      title: 'Assistance Médicale', 
      icon: 'medkit-outline', 
      color: '#3182CE', 
      bgColor: '#EBF8FF',
      image: require('../../assets/images/professional-workers-group-doctor-man-600nw-.webp'),
      route: '/services/medical'
    },
    { 
      id: 'legal', 
      title: 'Support Juridique', 
      icon: 'shield-checkmark-outline', 
      color: '#38A169', 
      bgColor: '#E6FFFA',
      image: require('../../assets/images/statue-justice-on-lawyers-desk-600nw-2589689745.webp'),
      route: '/services/legal'
    },
    { 
      id: 'forum', 
      title: 'Communauté', 
      icon: 'people-outline', 
      color: '#805AD5', 
      bgColor: '#FAF5FF',
      image: require('../../assets/images/young-indian-woman-sits-alone-600nw-2442275081.webp'),
      route: '/services/forum'
    },
    { 
      id: 'health', 
      title: 'Suivi Santé', 
      icon: 'heart-outline', 
      color: '#E53E3E', 
      bgColor: '#FFF5F5',
      image: require('../../assets/images/domestic-violence-awareness-month-background-600nw-2324617203.webp'),
      route: '/services/health'
    },
  ];

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.title}>Services Bomoko</Text>
      <Text style={styles.subtitle}>Accédez à nos services spécialisés pour votre protection et votre bien-être.</Text>
      
      <View style={styles.gridContainer}>
        {services.map((service) => (
          <TouchableOpacity 
            key={service.id} 
            style={styles.serviceItem}
            activeOpacity={0.8}
            onPress={() => router.push(service.route as any)}
          >
            <Image source={service.image} style={styles.cardImage} />
            <View style={styles.cardContent}>
              <View style={[styles.iconBox, { backgroundColor: service.bgColor }]}>
                <Ionicons name={service.icon as any} size={24} color={service.color} />
              </View>
              <Text style={styles.serviceLabel}>{service.title}</Text>
            </View>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.infoCard}>
        <Ionicons name="information-circle-outline" size={24} color="#3182CE" />
        <Text style={styles.infoText}>
          Tous nos services sont gratuits et confidentiels pour les membres de la communauté Bomoko.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#F7FAFC',
  },
  scrollContent: {
    padding: 20,
    paddingBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '900',
    color: '#2D3748',
  },
  subtitle: {
    fontSize: 16,
    color: '#718096',
    marginTop: 8,
    marginBottom: 32,
    lineHeight: 24,
  },
  gridContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  serviceItem: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    marginBottom: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 4,
  },
  cardImage: {
    width: '100%',
    height: 100,
    backgroundColor: '#EDF2F7',
  },
  cardContent: {
    padding: 16,
    alignItems: 'center',
  },
  iconBox: {
    width: 48,
    height: 48,
    borderRadius: 14,
    marginBottom: 12,
    marginTop: -40,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  serviceLabel: {
    fontSize: 14,
    fontWeight: '800',
    color: '#2D3748',
    textAlign: 'center',
    lineHeight: 20,
  },
  infoCard: {
    marginTop: 24,
    backgroundColor: '#EBF8FF',
    borderRadius: 16,
    padding: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  infoText: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: '#2C5282',
    lineHeight: 20,
  }
});
