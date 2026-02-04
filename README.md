# Discord Todo Bot

A Discord bot for managing to-do lists with slash commands. Tasks are stored per channel; daily reminders post incomplete tasks to a configured channel and move completed ones to a "done" channel.
Main motiviation: wanted bot to selfhost

## Commands

| Command | Description |
|--------|-------------|
| `/add task` | Add a task (use `\|` for details, e.g. `Buy milk \| 2% gallon`) |
| `/list` | List tasks in this channel |
| `/listall` | List tasks from all channels |
| `/done` | Mark a task as completed |
| `/edit` | Edit a task's name or details |
| `/remove` | Delete task(s) |
| `/help` | Show help |

## Setup

### 1. Create a Discord application and bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications) → New Application.
2. Under **Bot**, create a bot and copy the **Token**.
3. Under **OAuth2 → URL Generator**, select scopes `bot` and `applications.commands`, then copy the generated URL and open it to invite the bot to your server.

### 2. Environment variables

Create a `.env` file in the project root:

```env
DISCORD_TOKEN=your_bot_token_here
```

Optional:

- `DISCORD_USERNAME_ID` – User or role ID to mention in daily reminders (default: `@everyone`).
- `DATA_DIR` – Directory for the todo JSON file (default: current directory; used by Docker as `/data`).

### 3. Run the bot

**Option A – Local (Python 3.11+)**

```bash
pip install -r docker/requirements.txt
python bot.py
```

**Option B – Docker**

```bash
chmod +x docker_startup.sh
./docker_startup.sh
```

This builds the image, runs the container, and mounts `.env` and a data directory. By default the todo file is `discord_bot_list.json` in the project directory. To use another path:

```bash
./docker_startup.sh /path/to/your_todos.json
```

- Logs: `docker logs -f discord-todo-bot`
- Stop: `docker stop discord-todo-bot`

### 4. Discord channels (for reminders)

For daily reminders to work, create these text channels (or adjust names in `utility/storage.py`):

- **to-do** – channels that receive the daily reminder of incomplete tasks.
- **done-tasks** – channel where completed tasks are posted when the reminder runs (9:00 AM America/Los_Angeles).

## Requirements

- Python 3.11+ (local) or Docker
- `discord.py>=2.0.0`, `python-dotenv>=1.0.0`
