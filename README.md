# 🕵️ OSINT Telegram Bot

Bot Telegram OSINT complet avec **boutons inline**, **FSM** et déploiement **Render**.

## 🚀 Déploiement sur Render (recommandé)

### 1. Fork / clone le repo
```bash
git clone https://github.com/glm02/osint-telegram-bot
```

### 2. Créer le service sur Render
1. Aller sur [render.com](https://render.com) → **New → Web Service**
2. Connecter ce repo GitHub
3. Render détecte automatiquement `render.yaml`
4. Remplir les variables d'environnement :

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Token BotFather |
| `WEBHOOK_URL` | URL publique Render (ex: `https://osint-bot-xxxx.onrender.com`) |
| `HIBP_API_KEY` | Clé HaveIBeenPwned (~3.50$/mois) |
| `VERIPHONE_API_KEY` | Clé Veriphone (1000 req/mois gratuit) |
| `ADMIN_IDS` | Ton user ID Telegram |

### 3. Déployer
Cliquer **Deploy** — Render lance `pip install -r requirements.txt` puis `python bot.py`.

> ⚠️ **Important** : colle l'URL Render dans `WEBHOOK_URL` *avant* de déployer.

---

## 💻 Dev local (polling)

```bash
pip install -r requirements.txt
cp .env.example .env
# Laisser WEBHOOK_URL vide dans .env
python bot.py
```

---

## 📋 Commandes & Boutons

Le bot utilise un **menu inline à boutons** — plus besoin de taper les commandes.
Les commandes `/` restent disponibles en parallèle.

```
/start         → Menu principal (boutons)
/annuler       → Annuler la saisie en cours
```

## ⚠️ Avertissement légal

Usage éducatif et légal uniquement. Toute utilisation abusive relève de la responsabilité de l'utilisateur.
