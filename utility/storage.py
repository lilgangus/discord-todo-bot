import json
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv("DISCORD_TOKEN")
DATA_DIR = os.getenv("DATA_DIR", ".")
TODO_FILE = os.path.join(DATA_DIR, (sys.argv[1] if len(sys.argv) > 1 else "discord_bot_list") + ".json")
REMINDER_HOUR = 9
REMINDER_MINUTE = 0
REMINDER_MENTION = os.getenv("DISCORD_USERNAME_ID", "@everyone")
REMINDER_CHANNELS = ["to-do"]  # List of channel names to send daily reminders to
DONE_CHANNEL = "done-tasks"  # Channel to post removed/completed tasks

# In-memory storage for todos (per guild, per channel)
# Structure: todos[guild_id][channel_id] = [tasks...]
todos = {}


def load_todos():
    """Load todos from file."""
    global todos
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as f:
            data = json.load(f)
            # Convert string keys back to integers (JSON stores keys as strings)
            todos = {
                int(guild_id): {
                    int(channel_id): tasks
                    for channel_id, tasks in channels.items()
                }
                for guild_id, channels in data.items()
            }


def save_todos():
    """Save todos to file."""
    with open(TODO_FILE, "w") as f:
        json.dump(todos, f, indent=2)


# Load existing todos on startup
load_todos()
