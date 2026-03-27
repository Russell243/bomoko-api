# Guide de Déploiement Google Cloud - Bomoko

Ce guide contient toutes les commandes nécessaires pour déployer l'API Bomoko sur Google Cloud Platform (GCP).

**ID du Projet :** `cleveland-467300-d1`
**Région :** `europe-west9` (Paris)

---

## 1. Préparation de l'Infrastructure

### Activer les APIs
```bash
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com compute.googleapis.com
```

### Créer la Base de Données (PostgreSQL)
```bash
gcloud sql instances create bomoko-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=europe-west9
```

### Créer la base de données et l'utilisateur
Une fois l'instance créée :
```bash
gcloud sql databases create bomoko_db --instance=bomoko-db
gcloud sql users set-password postgres --instance=bomoko-db --password=BOMOKO_SAFE_PASSWORD_123
```

---

## 2. Gestion des Secrets

### Synchroniser le fichier .env vers Google Secrets
Installe d'abord la bibliothèque nécessaire :
```bash
pip install google-cloud-secret-manager
```
Puis lance le script que j'ai créé :
```bash
python sync_secrets.py
```

---

## 3. Déploiement sur Cloud Run

### Lancer le déploiement
```bash
gcloud run deploy bomoko-api --source . --region=europe-west9 --allow-unauthenticated --add-cloudsql-instances=cleveland-467300-d1:europe-west9:bomoko-db
```

### Après le déploiement
L'URL de ton API s'affichera (ex: `https://bomoko-api-xyz.a.run.app`). 
Il faudra alors mettre à jour la variable `EXPO_PUBLIC_API_URL` dans ton fichier `.env` du dossier **bomoko-mobile**.
