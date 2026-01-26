#!/bin/bash

# Discord Todo Bot - Docker Startup Script
# Usage: ./docker_startup.sh [filepath]
# Example: ./docker_startup.sh /path/to/my_todos.json

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Use provided filepath or default to project directory
if [ -n "$1" ]; then
    TODO_FILE="$1"
else
    TODO_FILE="$PROJECT_DIR/discord_bot_list.json"
fi

# Get absolute path and directory
TODO_FILE="$(cd "$(dirname "$TODO_FILE")" 2>/dev/null && pwd)/$(basename "$TODO_FILE")"
TODO_DIR="$(dirname "$TODO_FILE")"
TODO_NAME="$(basename "$TODO_FILE" .json)"

echo "Starting bot with todo file: $TODO_FILE"
# Build the image from project root
docker build -t discord-todo-bot -f "$PROJECT_DIR/docker/Dockerfile" "$PROJECT_DIR"

# Run the Docker container
docker run -d \
    --name discord-todo-bot \
    --restart unless-stopped \
    -v "$TODO_DIR:/data" \
    -v "$PROJECT_DIR/.env:/app/.env:ro" \
    discord-todo-bot "$TODO_NAME"

echo "Bot started! Container name: discord-todo-bot"
echo "View logs: docker logs -f discord-todo-bot"
echo "Stop bot:  docker stop discord-todo-bot"
