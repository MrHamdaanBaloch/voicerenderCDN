# AuraVoice AI Agent

AuraVoice is a real-time, humanlike AI voice agent capable of handling concurrent calls. It uses SignalWire for call handling, Celery for task queuing, and Groq for fast STT, LLM, and TTS processing.

## 🚀 Getting Started

### Prerequisites

*   Docker and Docker Compose
*   A SignalWire account with a provisioned phone number
*   A Groq Cloud account and API key
*   (Optional) An Anthropic account and API key for the fallback LLM

### 1. Configure Environment Variables

Create a `.env` file in the project root by copying the `.env.example` (if one existed) or creating a new one. Fill in the required credentials:

```env
# SignalWire API Credentials
SIGNALWIRE_PROJECT_ID=YOUR_PROJECT_ID
SIGNALWIRE_TOKEN=YOUR_API_TOKEN
SIGNALWIRE_CONTEXT=office

# Groq API Key
GROQ_API_KEY=YOUR_GROQ_API_KEY

# Anthropic API Key (for fallback LLM)
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# STT Configuration
WHISPER_MODEL_SIZE=base.en

# Public URL for TTS Playback
# IMPORTANT: This must be a publicly accessible URL pointing to a directory
# where TTS audio files can be served. For local development, use ngrok.
PUBLIC_URL_BASE=http://your-ngrok-public-url.io
```

### 2. Local Development with Ngrok

The Celery task saves the generated TTS audio to a temporary directory within the `celery_worker` container (`/tmp`). To play this audio back on the call, SignalWire needs a public URL to fetch the audio file from.

1.  **Start a simple HTTP server** inside the Celery container to serve the `/tmp` directory. You can do this by modifying the `command` in the `docker-compose.yml` for the `celery_worker` service or by running a separate command.

2.  **Expose the HTTP server port** (e.g., 8001) from the `celery_worker` service in your `docker-compose.yml`.

3.  **Use ngrok** to create a public tunnel to that port:
    ```bash
    ngrok http 8001
    ```

4.  **Update `PUBLIC_URL_BASE`** in your `.env` file with the public URL provided by ngrok (e.g., `http://1a2b-3c4d-5e6f.ngrok.io`).

### 3. Running the Application

With Docker and Docker Compose installed, and your `.env` file configured, you can start the entire application stack with a single command:

```bash
docker-compose up --build
```

This will:
*   Build the Docker image for the application.
*   Start the Redis container.
*   Start the Celery worker container.
*   Start the main application container running `relay_server.py`.

### 4. Point SignalWire to Your Application

In your SignalWire dashboard, configure your phone number to handle incoming calls by pointing it to your application. The handler should be set to **Relay**, and the context should match the `SIGNALWIRE_CONTEXT` in your `.env` file (e.g., `office`).

### 5. Make a Call

Call your SignalWire phone number. The `relay_server` will answer, and you can start a conversation with the AI agent. Check the logs for detailed output:

```bash
docker-compose logs -f
