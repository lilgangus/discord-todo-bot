FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot files
COPY bot.py ./
COPY utility/ ./utility/

# Create data directory for mounted volume
RUN mkdir -p /data

# Set data directory for storage
ENV DATA_DIR=/data

# Run the bot (filename passed as argument)
ENTRYPOINT ["python", "bot.py"]
CMD ["discord_bot_list"]
