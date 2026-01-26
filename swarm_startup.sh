#!/bin/bash
# This script manages the Discord Todo Bot service in swarm mode
#
# USAGE:
#   ./swarm_startup.sh <env_file> <json_file>
#
# ARGUMENTS:
#   env_file   - Path to .env file containing DISCORD_TOKEN (required)
#   json_file  - Path to JSON data file (required, created if doesn't exist)
#

# Upload to docker hub with:
#     docker build -t discord-todo-bot -f docker/Dockerfile .
#     docker tag discord-todo-bot lilgangus/discord-todo-bot:latest
#     docker push lilgangus/discord-todo-bot:latest

# Update swarm runing container with:
    # docker service update --image lilgangus/discord-todo-bot:latest --force discord-todo-bot

SERVICE_NAME="discord-todo-bot"
IMAGE="${DISCORD_BOT_IMAGE:-lilgangus/discord-todo-bot:latest}"
TARGET_NODE="${TARGET_NODE:-orion1}"

# Env file (required argument)
ENV_FILE="${1:-}"

# JSON file (required argument)
JSON_FILE="${2:-}"

# Validate arguments
if [ -z "$ENV_FILE" ] || [ -z "$JSON_FILE" ]; then
    echo "Error: Both env file and json file are required"
    echo "Usage: $0 <env_file> <json_file>"
    echo "Example: $0 /opt/secrets/.env /opt/data/todos.json"
    exit 1
fi

# Convert env file to absolute path (this file IS on the manager node)
if [[ "$ENV_FILE" != /* ]]; then
    ENV_FILE="$(cd "$(dirname "$ENV_FILE")" 2>/dev/null && pwd)/$(basename "$ENV_FILE")"
fi

# JSON file path must be an absolute path on the TARGET node - don't convert locally
if [[ "$JSON_FILE" != /* ]]; then
    echo "Error: JSON file path must be an absolute path (on the target node)"
    echo "Example: /opt/data/todos.json"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    echo "Please create it with your Discord token:"
    echo "  echo 'DISCORD_TOKEN=your_token_here' > $ENV_FILE"
    exit 1
fi

# Get JSON directory and filename
JSON_DIR="$(dirname "$JSON_FILE")"
TODO_NAME="$(basename "$JSON_FILE" .json)"

# NOTE: We cannot validate if JSON_DIR exists because it's on the TARGET node, not this machine.
# The bind mount will fail at runtime if the directory doesn't exist on the target node.

echo "========================================"
echo "Discord Todo Bot - Swarm Deployment"
echo "========================================"
echo "Service name: $SERVICE_NAME"
echo "Image: $IMAGE"
echo "Target node: $TARGET_NODE"
echo "Env file: $ENV_FILE (read from this machine)"
echo "Data directory: $JSON_DIR (must exist on $TARGET_NODE)"
echo "Todo file: $TODO_NAME.json"
echo "========================================"
echo ""
echo "NOTE: Ensure the following exists on $TARGET_NODE:"
echo "  mkdir -p $JSON_DIR"
echo ""

# Function to check if service exists
service_exists() {
    docker service ls --format '{{.Name}}' | grep -q "^${SERVICE_NAME}$"
}

# Function to wait for service removal
wait_for_removal() {
    echo "Waiting for service to be fully removed..."
    local count=0
    while service_exists && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
    done
}

# Stop and remove existing service if it exists
if service_exists; then
    echo "Removing existing Discord Todo Bot service..."
    docker service rm "$SERVICE_NAME"
    wait_for_removal
fi

# Create the service
echo "Creating Discord Todo Bot service on node $TARGET_NODE..."
docker service create \
    --name "$SERVICE_NAME" \
    --constraint "node.hostname==$TARGET_NODE" \
    --mount type=bind,source="$JSON_DIR",target=/data \
    --env-file "$ENV_FILE" \
    --restart-condition any \
    --with-registry-auth \
    "$IMAGE" "$TODO_NAME"

# Wait for the service to initialize
echo "Waiting for service to start..."
sleep 5

# Check if service was created successfully
if service_exists; then
    # Get task status
    TASK_STATE=$(docker service ps "$SERVICE_NAME" --format '{{.CurrentState}}' | head -n1)
    
    echo ""
    echo "========================================"
    echo "✓ Discord Todo Bot service created!"
    echo "========================================"
    echo "  Service: $SERVICE_NAME"
    echo "  Node: $TARGET_NODE"
    echo "  Todo file: $JSON_DIR/$TODO_NAME.json (on $TARGET_NODE)"
    echo "  Current state: $TASK_STATE"
    echo ""
    echo "Useful commands:"
    echo "  View status:  docker service ps $SERVICE_NAME"
    echo "  View logs:    docker service logs -f $SERVICE_NAME"
    echo "  Remove:       docker service rm $SERVICE_NAME"
    echo "  Update image: docker service update --image $IMAGE $SERVICE_NAME"
    echo "========================================"
else
    echo ""
    echo "========================================"
    echo "✗ Failed to create Discord Todo Bot service"
    echo "========================================"
    echo "Troubleshooting:"
    echo "  1. Check if the image exists: docker pull $IMAGE"
    echo "  2. Check if target node exists: docker node ls"
    echo "  3. Check if files exist on $TARGET_NODE:"
    echo "     - $ENV_FILE"
    echo "     - $JSON_FILE"
    echo "  4. Check swarm logs: docker service ps $SERVICE_NAME --no-trunc"
    echo "========================================"
    exit 1
fi
