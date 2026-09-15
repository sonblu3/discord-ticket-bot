# Discord Support Ticket Bot 🎫

A lightweight Discord support ticket bot built with `discord.py`.

## Features

- 🎫 Create tickets with a dropdown menu
- 🛒 Purchase & information category
- 🛠️ Technical support category
- 🔄 Upgrade & renewal category
- 📄 Refund & complaint category
- 🔒 Close tickets with a button
- 📝 Automatically generate a text transcript
- 📩 Send the transcript to the ticket opener by DM
- ⏰ Automatically close inactive tickets
- 🚫 Prevent users from opening duplicate tickets
- 🔐 Configuration through environment variables
- ☁️ No VPS-specific code — can run anywhere Python/Discord bots are supported

## Requirements

- Python 3.10+
- A Discord application/bot
- The bot needs permission to:
  - Manage Channels
  - Send Messages
  - Read Message History
  - Attach Files
  - View Channels

The bot also uses the Discord **Message Content Intent**, so enable it in the Discord Developer Portal.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env`

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```env
DISCORD_TOKEN=YOUR_BOT_TOKEN
OWNER_ID=123456789012345678
TICKET_CATEGORY_ID=123456789012345678
TICKET_NUMBER=0
INACTIVITY_DAYS=7
```

### 4. Start the bot

```bash
python bot.py
```

## Usage

Once the bot is online, the configured owner can run:

```text
/ticket
```

The bot will send the support ticket panel.

Users select a support category and a private ticket channel is created automatically.

## Security

**Never upload your real bot token to GitHub.**

Keep your real credentials inside `.env`.

The repository includes `.gitignore` so `.env` is ignored automatically.

If a bot token is accidentally exposed, regenerate it immediately in the Discord Developer Portal.

## Project structure

```text
.
├── bot.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## License

MIT License — see `LICENSE`.
