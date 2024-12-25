# Use Python 3.9 as the base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire code base into the container
COPY . /app/

# Set the environment variables for MongoDB and Telegram API Token
ENV TELEGRAM_API_TOKEN=<Your_Token_Here>
ENV MONGO_URL=<Your_Mongo_Connection_URL>

# Run bot.py when the container starts
CMD ["python", "bot.py"]
