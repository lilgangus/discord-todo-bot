import discord
from discord import ui

from utility.storage import todos, save_todos, DONE_CHANNEL


class DoneTaskSelect(ui.Select):
    def __init__(self, guild_id, channel_id):
        self.guild_id = guild_id
        self.channel_id = channel_id
        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        # Only show incomplete tasks
        incomplete_tasks = [task for task in channel_tasks if not task["done"]]
        options = [
            discord.SelectOption(
                label=f"#{task['id']} {task['name'][:50]}",
                value=str(task["id"]),
                description=task["details"][:100] if task["details"] else None
            )
            for task in incomplete_tasks
        ]
        super().__init__(placeholder="Select a task to mark as done...", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_id = int(self.values[0])
        guild_id = self.guild_id
        channel_id = self.channel_id

        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        for task in channel_tasks:
            if task["id"] == task_id:
                task["done"] = True
                save_todos()
                await interaction.response.send_message(f"Task #{task_id} marked as done: **{task['name']}**")
                await interaction.message.delete()
                return


class DoneTaskView(ui.View):
    def __init__(self, guild_id, channel_id):
        super().__init__(timeout=60)
        self.add_item(DoneTaskSelect(guild_id, channel_id))

    async def on_timeout(self):
        pass


class EditTaskModal(ui.Modal):
    def __init__(self, guild_id, channel_id, task_id, task_name, task_details):
        super().__init__(title="Edit Task")
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.task_id = task_id

        self.name_input = ui.TextInput(
            label="Task Name",
            default=task_name,
            max_length=100
        )
        self.details_input = ui.TextInput(
            label="Details",
            default=task_details,
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500
        )
        self.add_item(self.name_input)
        self.add_item(self.details_input)

    async def on_submit(self, interaction: discord.Interaction):
        channel_tasks = todos.get(self.guild_id, {}).get(self.channel_id, [])
        for task in channel_tasks:
            if task["id"] == self.task_id:
                task["name"] = self.name_input.value
                task["details"] = self.details_input.value
                save_todos()
                await interaction.response.send_message(
                    f"Task #{self.task_id} updated: **{task['name']}**"
                )
                return


class EditTaskSelect(ui.Select):
    def __init__(self, guild_id, channel_id):
        self.guild_id = guild_id
        self.channel_id = channel_id
        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        options = [
            discord.SelectOption(
                label=f"#{task['id']} {task['name'][:50]}",
                value=str(task["id"]),
                description=task["details"][:100] if task["details"] else None
            )
            for task in channel_tasks
        ]
        super().__init__(placeholder="Select a task to edit...", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_id = int(self.values[0])
        guild_id = self.guild_id
        channel_id = self.channel_id

        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        for task in channel_tasks:
            if task["id"] == task_id:
                modal = EditTaskModal(
                    guild_id, channel_id, task_id,
                    task["name"], task["details"]
                )
                await interaction.response.send_modal(modal)
                await interaction.message.delete()
                return


class EditTaskView(ui.View):
    def __init__(self, guild_id, channel_id):
        super().__init__(timeout=60)
        self.add_item(EditTaskSelect(guild_id, channel_id))

    async def on_timeout(self):
        pass


class RemoveTaskSelect(ui.Select):
    def __init__(self, guild_id, channel_id):
        self.guild_id = guild_id
        self.channel_id = channel_id
        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        options = [
            discord.SelectOption(
                label=f"#{task['id']} {task['name'][:50]}",
                value=str(task["id"]),
                description=task["details"][:100] if task["details"] else None
            )
            for task in channel_tasks
        ]
        # Allow selecting multiple tasks (up to 25, Discord's limit)
        max_selections = min(len(options), 25)
        super().__init__(
            placeholder="Select task(s) to remove...",
            options=options,
            min_values=1,
            max_values=max_selections
        )

    async def callback(self, interaction: discord.Interaction):
        task_ids = [int(v) for v in self.values]
        guild_id = self.guild_id
        channel_id = self.channel_id

        # Get source channel name
        source_channel = interaction.guild.get_channel(channel_id)
        source_channel_name = source_channel.name if source_channel else f"Unknown ({channel_id})"

        channel_tasks = todos.get(guild_id, {}).get(channel_id, [])
        removed_tasks = []

        # Remove tasks (iterate in reverse to avoid index issues)
        for task_id in task_ids:
            for i, task in enumerate(channel_tasks):
                if task["id"] == task_id:
                    removed = channel_tasks.pop(i)
                    removed_tasks.append(removed)
                    break

        if removed_tasks:
            save_todos()

            # Post to done channel
            done_channel = discord.utils.get(interaction.guild.channels, name=DONE_CHANNEL)
            if done_channel:
                message = f"**Tasks Removed from #{source_channel_name}:**\n"
                for removed in removed_tasks:
                    status = "[x]" if removed["done"] else "[ ]"
                    details_text = f" - {removed['details']}" if removed["details"] else ""
                    message += f"{status} {removed['name']}{details_text}\n"
                await done_channel.send(message)

            # Send confirmation
            task_names = ", ".join([f"**{t['name']}**" for t in removed_tasks])
            await interaction.response.send_message(f"Removed {len(removed_tasks)} task(s): {task_names}")
            await interaction.message.delete()


class RemoveTaskView(ui.View):
    def __init__(self, guild_id, channel_id):
        super().__init__(timeout=60)
        self.add_item(RemoveTaskSelect(guild_id, channel_id))

    @ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()

    async def on_timeout(self):
        pass
