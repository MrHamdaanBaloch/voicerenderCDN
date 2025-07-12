# How to Deploy the TTS Orchestrator to Render

This guide will walk you through deploying the `tts_orchestrator.py` service to Render. This will give you a stable, public URL that eliminates the need for `ngrok` or other tunneling services.

## Step 1: Prepare Your GitHub Repository

1.  **Create a GitHub Account:** If you don't have one, sign up at [github.com](https://github.com).
2.  **Create a New Repository:** Create a new, public repository for this project.
3.  **Push Your Code:** Upload all the project files (`tts_orchestrator.py`, `relay_server.py`, `celery_worker/`, `requirements.txt`, `render.yaml`, `.env`, etc.) to this new repository.

## Step 2: Create and Configure the Render Service

1.  **Create a Render Account:** Sign up at [dashboard.render.com](https://dashboard.render.com). You can sign up using your GitHub account, which makes the process easier.
2.  **Create a New Blueprint Service:**
    *   On the Render dashboard, click the **"New +"** button.
    *   Select **"Blueprint"**.
    *   Connect your GitHub account to Render.
    *   Select the repository you just created. Render will automatically detect and parse your `render.yaml` file.
3.  **Name Your Service:** Give the new service group a name, like `aura-voice-services`.
4.  **Review and Create:** Render will show you the service it's about to create based on the `render.yaml` file (`tts-orchestrator`). Click **"Apply"** or **"Create New Services"**.

## Step 3: Set Your Environment Variables

Render will not read your `.env` file for security reasons. You must set your secrets in the Render dashboard.

1.  After the service is created, navigate to its dashboard.
2.  Go to the **"Environment"** tab.
3.  Under **"Secret Files"**, you can create a `.env` file and paste the contents of your local `.env` file into it.
4.  Alternatively, under **"Environment Variables"**, you need to add a secret for `GROQ_API_KEY`.
    *   Click **"Add Environment Variable"**.
    *   For the **Key**, enter `GROQ_API_KEY`.
    *   For the **Value**, paste your actual Groq API key.
    *   Click **"Save Changes"**.

## Step 4: Get Your Public URL

1.  Render will automatically start building and deploying your service. You can watch the progress in the **"Events"** or **"Logs"** tab.
2.  Once the deployment is successful, you will see a "Live" status.
3.  At the top of the service page, you will find the public URL for your TTS orchestrator. It will look something like `https://tts-orchestrator.onrender.com`.
4.  **This is your `TTS_ORCHESTRATOR_URL`**.

## Step 5: Update Your Local `.env` File

1.  Take the public URL from Render.
2.  Open your local `.env` file.
3.  Add or update the `TTS_ORCHESTRATOR_URL` variable:
    ```
    TTS_ORCHESTRATOR_URL=https://tts-orchestrator.onrender.com
    ```

## Final Step: Run Your Local Services

Your TTS service is now running professionally in the cloud. You no longer need to run `uvicorn` or a tunnel locally.

You only need to run your local components:
1.  **Redis:** `docker-compose up -d redis`
2.  **Celery Worker:** `celery -A celery_worker.celery_app worker --loglevel=info`
3.  **Relay Server:** `python relay_server.py`

The system is now fully deployed and ready for production-level performance.
