from datetime import time
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utility.storage import (
    TOKEN,
    REMINDER_HOUR,
    REMINDER_MINUTE,
    REMINDER_MENTION,
    REMINDER_CHANNELS,
    DONE_CHANNEL,
    todos,
    save_todos,
)
from utility.ui_components import (
    DoneTaskView,
    EditTaskView,
    RemoveTaskView,
)

# note that guild = server

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Show all available commands."""
    help_text = """**Todo Bot Commands**

- **/add task** - Add a new task (use `|` for details, e.g. `Buy milk | 2% gallon`)
- **/list** - Show all tasks in this channel
- **/listall** - Show all tasks from all channels
- **/done** - Mark a task as completed (dropdown selector)
- **/edit** - Edit a task's name or details (dropdown + modal)
- **/remove** - Delete task(s) (multi-select dropdown)
- **/help** - Show this help message
"""
    await interaction.response.send_message(help_text)


@tasks.loop(time=time(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, tzinfo=ZoneInfo("America/Los_Angeles")))
async def daily_reminder():
    """Send daily reminder of incomplete tasks to specified channels."""
    # Format mention (user ID becomes <@id>, otherwise use as-is)
    mention = f"<@{REMINDER_MENTION}>" if REMINDER_MENTION.isdigit() else REMINDER_MENTION

    for guild in bot.guilds:
        guild_id = guild.id
        done_channel = discord.utils.get(guild.text_channels, name=DONE_CHANNEL)

        # Send to each channel in REMINDER_CHANNELS
        for channel_name in REMINDER_CHANNELS:
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not channel:
                continue

            channel_id = channel.id
            channel_tasks = todos.get(guild_id, {}).get(channel_id, [])

            # Separate done and incomplete tasks
            done_tasks = [task for task in channel_tasks if task["done"]]
            incomplete = [task for task in channel_tasks if not task["done"]]

            # Remove done tasks and log to done channel
            if done_tasks and done_channel:
                message = f"**Completed Tasks from #{channel_name}:**\n"
                for task in done_tasks:
                    details_text = f" - {task['details']}" if task["details"] else ""
                    message += f"[x] #{task['id']} **{task['name']}**{details_text}\n"
                await done_channel.send(message)

            # Remove done tasks from the list
            if done_tasks:
                todos[guild_id][channel_id] = incomplete
                save_todos()

            # Send reminder for incomplete tasks
            if not incomplete:
                await channel.send(f"{mention} **Daily Task Reminder:**\nNo tasks!")
            else:
                message = f"{mention} **Daily Task Reminder:**\n"
                for task in incomplete:
                    details_text = f" - {task['details']}" if task["details"] else ""
                    message += f"[ ] #{task['id']} **{task['name']}**{details_text}\n"
                await channel.send(message)


@bot.event
async def on_ready():
    daily_reminder.start()
    # Sync slash commands with Discord
    await bot.tree.sync()
    print(f"{bot.user} is now online!")
    print("Slash commands synced!")


@bot.tree.command(name="add", description="Add a new task to this channel")
@app_commands.describe(task="Task name, optionally followed by | and details")
async def add(interaction: discord.Interaction, task: str):
    """Add a new task."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id

    if guild_id not in todos:
        todos[guild_id] = {}
    if channel_id not in todos[guild_id]:
        todos[guild_id][channel_id] = []

    # Parse task name and details
    if "|" in task:
        parts = task.split("|", 1)
        taskname = parts[0].strip()
        details = parts[1].strip()
    else:
        taskname = task.strip()
        details = ""

    task_id = max((t["id"] for t in todos[guild_id][channel_id]), default=0) + 1
    todos[guild_id][channel_id].append({
        "id": task_id,
        "name": taskname,
        "details": details,
        "done": False
    })

    save_todos()
    await interaction.response.send_message(f"Task #{task_id} added: **{taskname}**")


@bot.tree.command(name="list", description="Show all tasks in this channel")
async def list_tasks(interaction: discord.Interaction):
    """List all tasks in this channel."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    channel_name = interaction.channel.name

    channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
    if not channel_tasks:
        await interaction.response.send_message("No tasks yet. Add one with `/add`")
        return

    message = f"**#{channel_name} List:**\n"
    for task in channel_tasks:
        status = "[x]" if task["done"] else "[ ]"
        details_text = f" - {task['details']}" if task["details"] else ""
        message += f"{status} #{task['id']} **{task['name']}**{details_text}\n"

    await interaction.response.send_message(message)


@bot.tree.command(name="listall", description="Show all tasks from all channels")
async def list_all_tasks(interaction: discord.Interaction):
    """List all tasks from all channels."""
    guild_id = interaction.guild_id

    guild_todos = todos.get(guild_id, {})
    if not guild_todos:
        await interaction.response.send_message("No tasks in any channel.")
        return

    message = "**All Tasks:**\n"
    has_tasks = False

    for channel_id, channel_tasks in guild_todos.items():
        if not channel_tasks:
            continue

        channel = interaction.guild.get_channel(channel_id)
        channel_name = channel.name if channel else f"Unknown ({channel_id})"

        message += f"\n**#{channel_name}:**\n"
        for task in channel_tasks:
            status = "[x]" if task["done"] else "[ ]"
            details_text = f" - {task['details']}" if task["details"] else ""
            message += f"{status} #{task['id']} **{task['name']}**{details_text}\n"
        has_tasks = True

    if not has_tasks:
        await interaction.response.send_message("No tasks in any channel.")
        return

    await interaction.response.send_message(message)


@bot.tree.command(name="done", description="Mark a task as completed")
async def done(interaction: discord.Interaction):
    """Mark a task as done using a dropdown selector."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id

    channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
    incomplete_tasks = [task for task in channel_tasks if not task["done"]]

    if not incomplete_tasks:
        await interaction.response.send_message("No incomplete tasks found.")
        return

    view = DoneTaskView(guild_id, channel_id)
    await interaction.response.send_message("Select a task to mark as done:", view=view)


@bot.tree.command(name="edit", description="Edit a task's name or details")
async def edit(interaction: discord.Interaction):
    """Edit a task using a dropdown selector and modal."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id

    channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
    if not channel_tasks:
        await interaction.response.send_message("No tasks found.")
        return

    view = EditTaskView(guild_id, channel_id)
    await interaction.response.send_message("Select a task to edit:", view=view)


@bot.tree.command(name="remove", description="Delete a task from the list")
async def remove(interaction: discord.Interaction):
    """Remove a task using a dropdown selector."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id

    channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
    if not channel_tasks:
        await interaction.response.send_message("No tasks found.")
        return

    view = RemoveTaskView(guild_id, channel_id)
    await interaction.response.send_message("Select a task to remove:", view=view)


# Run the bot
bot.run(TOKEN)
