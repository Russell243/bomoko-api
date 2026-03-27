# Guide de Déploiement Supabase & Render - Bomoko

Puisque Google Cloud bloque sur la facturation, nous allons utiliser une combinaison gratuite et puissante : **Supabase** (pour la base de données) et **Render** (pour héberger ton API Django).

---

## 1. Créer la Base de Données sur Supabase

1. Va sur [supabase.com](https://supabase.com/) et connecte-toi avec ton compte GitHub ou Google.
2. Crée un nouveau projet nommé `bomoko-api`.
3. Choisis une région (ex: `Frankfurt` ou `Paris`).
4. **Important** : Définis un mot de passe pour ta base de données et **note-le bien**.
5. Une fois le projet créé, va dans :
   **Project Settings** > **Database** > **Connection string** > **URI**.
6. Copie cette URL. Elle ressemble à ceci :
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxx.supabase.co:5432/postgres`

---

## 2. Migration des données (SQLite vers Supabase)

1. J'ai créé un script spécial nommé `migrate_supabase.py` dans ton dossier.
2. Tu n'as pas besoin d'installer d'outils compliqués. Utilise simplement cette commande (remplace l'URL par la tienne) :
   ```bash
   python migrate_supabase.py "ton_url_supabase_ici"
   ```

---

## 3. Déploiement sur Render.com

1. Crée un compte sur [Render.com](https://render.com/).
2. Clique sur **"New"** > **"Web Service"**.
3. Connecte ton dépôt GitHub (ou télécharge ton code).
4. Configure les variables d'environnement dans l'onglet **Environment** de Render :
   - `DATABASE_URL` : (L'URL que tu as copiée de Supabase)
   - `SECRET_KEY` : (Celle de ton fichier .env actuel)
   - `DEBUG` : `False`
   - `ALLOWED_HOSTS` : `*` (ou l'URL que Render te donnera)

Render s'occupera de construire ton projet via ton `Dockerfile` automatiquement !
