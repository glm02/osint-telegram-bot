# 🕵️ OSINT Telegram Bot

Bot Telegram complet pour la reconnaissance OSINT en Python avec `aiogram`.

## 📋 Commandes disponibles

| Commande | Description |
|---|---|
| `/start` | Menu principal |
| `/sherlock <pseudo>` | Recherche pseudo sur 300+ réseaux sociaux |
| `/maigret <pseudo>` | Profil enrichi multi-sources |
| `/email <email>` | Comptes associés à un email (Holehe) |
| `/breach <email>` | Fuites de données (HaveIBeenPwned) |
| `/pwned <password>` | Vérification mot de passe compromis |
| `/phone <+33...>` | Analyse numéro de téléphone |
| `/ip <adresse>` | Géolocalisation + ASN + VPN detect |
| `/whois <domaine>` | Infos WHOIS |
| `/domain <domaine>` | Reconnaissance DNS (theHarvester) |

## ⚙️ Installation

```bash
git clone https://github.com/glm02/osint-telegram-bot
cd osint-telegram-bot
pip install -r requirements.txt
```

## 🔧 Configuration

Copie `.env.example` vers `.env` et remplis tes clés :

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=ton_token_botfather
HIBP_API_KEY=ta_cle_hibp
VERIPHONE_API_KEY=ta_cle_veriphone
ADMIN_IDS=123456789,987654321
```

### Obtenir les clés API
- **Telegram Token** → [@BotFather](https://t.me/BotFather)
- **HIBP API Key** → [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) (~3.50$/mois)
- **Veriphone** → [veriphone.io](https://veriphone.io) (1000 req/mois gratuit)

## 🚀 Lancement

```bash
python bot.py
```

### Déploiement Oracle Cloud (systemd)

```bash
sudo nano /etc/systemd/system/osint-bot.service
```

```ini
[Unit]
Description=OSINT Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/osint-telegram-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable osint-bot
sudo systemctl start osint-bot
```

## ⚠️ Avertissement légal

Ce bot est destiné à un usage **éducatif et légal uniquement** (pentest avec autorisation, recherches sur soi-même). Toute utilisation abusive est illégale et relève de la responsabilité de l'utilisateur.

## 📦 Dépendances

Voir `requirements.txt`
