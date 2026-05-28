# Intentions de Messes — Web App

Application de gestion des intentions de Messes avec insertion automatique et respect des règles de capacité.

## Fonctionnalités

- **Insérer** une intention avec déplacement automatique des sans-♦ si le jour est plein
- **Calendrier** mensuel avec visualisation des capacités et violations
- **Date libre** : trouver la prochaine date disponible (simple, neuvaine, trentain)
- **Violations** : détecter toutes les surcharges existantes dans la base

## Déploiement sur Railway

### 1. Prérequis
- Compte [Railway](https://railway.app) (gratuit)
- Compte GitHub
- Token d'intégration Notion (depuis notion.so → Settings → Integrations)

### 2. Déploiement

```bash
# 1. Pousser ce dossier sur GitHub (dépôt public ou privé)
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_NOM/intention-messe.git
git push -u origin main

# 2. Sur railway.app :
#    New Project → Deploy from GitHub repo → sélectionner le dépôt
#    Railway détecte automatiquement le Procfile
```

### 3. Variable d'environnement

Dans Railway → votre projet → Variables, ajouter :

```
NOTION_TOKEN = secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Le token se trouve dans notion.so → Settings → My Connections → Develop or manage integrations.  
L'intégration doit avoir accès à la base "Intentions de Messes".

### 4. Sécurité (optionnel mais recommandé)

Ajoutez une authentification basique en ajoutant ces variables Railway :

```
APP_USERNAME = votrelogin
APP_PASSWORD = votremotdepasse
```

Et décommentez le bloc `# AUTH` dans `app.py` (voir commentaires).

## Développement local

```bash
pip install -r requirements.txt
export NOTION_TOKEN=secret_xxx
uvicorn app:app --reload
# → http://localhost:8000
```

## Architecture

```
app.py          — Backend FastAPI + logique métier complète
templates/
  index.html    — Frontend HTML/CSS/JS (single-page)
requirements.txt
Procfile        — Point d'entrée Railway
```

## Règles métier implémentées

- Capacité variable selon le jour (1 standard, 2 dimanche/Ascension/Toussaint, 3 Noël/Commémoration, 1 en juillet-août)
- ♦ = intention fixe, ne se déplace pas sauf ordre explicite
- Périodes (neuvaine, trentain) : occupent chaque jour du bloc
- Inamovibles : intentions en cours (date_start ≤ aujourd'hui ≤ date_end)
- Préfixe `RIP -` automatique pour les défunts
- Déplacement récursif des sans-♦ avec rechargement Notion entre chaque
- Blocage et alerte sur conflit ♦/♦ ou inamovible saturant
