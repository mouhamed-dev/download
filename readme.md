# Téléchargeur de Médias - MouhaTech

![Couverture du projet](src/charge/static/charge/images/work.jpg)

Download.MouhaTech est une application web Django pour télécharger des vidéos, audios et miniatures depuis les plateformes de médias sociaux populaires.

## Description

Cette application permet aux utilisateurs de télécharger du contenu multimédia (vidéos, audios, miniatures) depuis diverses plateformes sociales en utilisant yt-dlp comme moteur de téléchargement principal et ffmpeg pour la conversion des fichiers. L'application offre une interface web simple avec suivi de progression en temps réel.

## Fonctionnalités

- **Téléchargement asynchrone** : Téléchargements en arrière-plan avec suivi de progression
- **Formats multiples** : Vidéo, audio (MP3) et miniatures
- **Qualités variables** : De la meilleure qualité à la qualité basique
- **Authentification automatique** : Utilisation de cookies pour les plateformes nécessitant une connexion
- **Support FFmpeg** : Intégré pour le traitement audio/vidéo
- **Interface web** : Formulaire simple et intuitif
- **Cache partagé** : Compatible multi-processus
- **Plateformes supportées** :
  - YouTube
  - Facebook
  - Instagram
  - TikTok
  - Twitter/X
  - Snapchat

## Prérequis

- Python 3.8+
- FFmpeg (optionnel, mais recommandé pour le traitement audio/vidéo)
- Navigateur web moderne

## Installation

1. **Cloner le dépôt** :

   ```bash
   git clone <url-du-depot>
   cd download
   ```

2. **Créer un environnement virtuel** :

   ```bash
   python -m venv env
   env\Scripts\activate  # Windows
   # ou
   source env/bin/activate  # Linux/Mac
   ```

3. **Installer les dépendances** :

   ```bash
   pip install -r src/requirements.txt
   ```

4. **Configurer l'environnement virtuel** :

   - Créer un fichier `.env` dans le dossier `src/charge/` avec les variables suivantes :
     ```bash
     SECRET_KEY=votre-cle-secrete-très-longue-et-complexe
     DEBUG=True
     ALLOWED_HOSTS=localhost,127.0.0.1
     ```

5. **Migrer la base de données** :

   ```bash
   cd src
   python manage.py migrate
   ```

6. **Lancer le serveur** :
   ```bash
   python manage.py runserver
   ```

L'application sera accessible sur `http://127.0.0.1:8000/`

## Configuration

### Cookies d'authentification

Pour télécharger du contenu nécessitant une authentification, placez les fichiers de cookies dans `src/download/cookies/` :

- `cookies_youtube.txt`
- `cookies_facebook.txt`
- `cookies_instagram.txt`
- `cookies_tiktok.txt`
- `cookies_twitter.txt`
- `cookies_snapchat.txt`

### FFmpeg

L'application recherche automatiquement FFmpeg dans :

1. Le dossier `src/download/ffmpeg/bin/`
2. Le PATH système

Pour utiliser une installation personnalisée, définissez `FFMPEG_LOCATION` dans votre fichier `.env`.

### Variables d'environnement

- `SECRET_KEY` : Clé secrète Django (obligatoire)
- `DEBUG` : Mode debug (True/False)
- `ALLOWED_HOSTS` : Hôtes autorisés (liste séparée par des virgules)
- `FFMPEG_LOCATION` : Chemin vers FFmpeg (optionnel)

## Utilisation

1. Ouvrez l'application dans votre navigateur
2. Collez l'URL du média à télécharger
3. Sélectionnez le type de média (vidéo/audio/miniature)
4. Choisissez la qualité souhaitée
5. Cliquez sur "Télécharger"
6. Suivez la progression en temps réel
7. Téléchargez le fichier une fois terminé

## API

L'application expose une API REST simple :

- `POST /start-download/` : Démarrer un téléchargement
- `GET /progress/<task_id>/` : Obtenir le statut d'un téléchargement
- `GET /download/<task_id>/` : Télécharger le fichier terminé

## Structure du projet

```
src/
├── charge/              # Application principale
│   ├── models.py       # Modèle MediaDownload
│   ├── views.py        # Logique de téléchargement
│   ├── forms.py        # Formulaire web
│   ├── templates/      # Templates HTML
│   └── static/         # Assets statiques
├── download/           # Configuration Django
│   ├── settings.py     # Paramètres
│   ├── urls.py         # Routage
│   ├── cookies/        # Fichiers de cookies
│   └── ffmpeg/         # Binaires FFmpeg
├── media/              # Fichiers téléchargés
├── cache/              # Cache Django
└── db.sqlite3          # Base de données
```

## Dépendances

- Django 5.2.8
- yt-dlp 2025.11.12
- ffmpeg-python 1.4
- django-environ 0.12.0

## Sécurité

- Utilisez des cookies valides et à jour
- Ne partagez pas vos fichiers de cookies
- En production, désactivez le mode DEBUG
- Configurez correctement ALLOWED_HOSTS

## Dépannage

### Erreur FFmpeg

Assurez-vous que FFmpeg est installé et accessible :

```bash
ffmpeg -version
```

### Cookies expirés

Régénérez vos cookies si les téléchargements échouent.

### Problèmes de quota

Certaines plateformes limitent les téléchargements non authentifiés.

## Licence

Ce projet est distribué sous licence MIT.  
Vous êtes libre de l’utiliser, le modifier et le redistribuer.  
Voir le fichier [LICENSE](Licence) pour plus de détails.

## Contribution

Les contributions sont les bienvenues !  
N’hésitez pas à ouvrir une issue pour signaler un problème ou à proposer une pull request pour des améliorations.

## Support

Pour les problèmes ou questions, créez une issue sur le dépôt GitHub.

## Soutenez le créateur ☕

Si ce dépôt vous a été utile, vous pouvez me soutenir avec un café afin de m’aider à couvrir les frais d’hébergement et à continuer à les améliorer.

<p align="center">
  <a href="TON_LIEN_DE_PAIEMENT" target="_blank"
     style="
       display:inline-block;
       padding:10px 18px;
       background:#791f87;
       color:white;
       text-decoration:none;
       border-radius:999px;
       font-weight:600;
       font-family:Arial, sans-serif;
     ">
    ☕ Offrir un café !
  </a>
</p>