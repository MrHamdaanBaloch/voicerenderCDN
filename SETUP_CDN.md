# How to Set Up Backblaze B2 for Audio Hosting

Follow these steps to create a public B2 bucket and get the API keys needed for our application.

## Step 1: Create a Backblaze Account

1.  Go to [https://www.backblaze.com/b2/sign-up.html](https://www.backblaze.com/b2/sign-up.html).
2.  Create a new account. You will get 10 GB of free storage.

## Step 2: Create a Public Bucket

1.  After logging in, on the left-hand menu, click on **"Buckets"**.
2.  Click the **"Create a Bucket"** button.
3.  Give your bucket a **unique name**. This name must be globally unique across all of Backblaze. For example: `aura-voice-audio-storage-12345`.
4.  Set the bucket's privacy to **"Public"**. This is critical so that SignalWire can access the audio files.
5.  Leave all other settings as their defaults and click **"Create a Bucket"**.

## Step 3: Get the Bucket's Public URL

1.  After the bucket is created, click on its name in the bucket list.
2.  Go to the **"Bucket Settings"** tab.
3.  Find the **"Endpoint URL"**. It will look something like `s3.us-west-004.backblazeb2.com`.
4.  Your public URL for files will be in the format: `https://<Your-Bucket-Name>.<Endpoint-URL>`.
    *   **Example:** `https://aura-voice-audio-storage-12345.s3.us-west-004.backblazeb2.com`
5.  Copy this base URL. You will need it later.

## Step 4: Create Application Keys

1.  On the left-hand menu, click on **"App Keys"**.
2.  Scroll down to the "Add a New Application Key" section.
3.  Give your key a name, like `aura-voice-worker`.
4.  Select the bucket you just created from the **"Allow access to Bucket(s)"** dropdown menu.
5.  For "Type of Access", select **"Read and Write"**.
6.  Click the **"Create New Key"** button.

## Step 5: Copy Your Credentials

**IMPORTANT:** You will only be shown the `applicationKey` **ONCE**. Copy it immediately and save it somewhere safe.

You will now have three pieces of information:
*   `keyID` (This is your Application Key ID)
*   `applicationKey` (This is your secret key)
*   The **Endpoint URL** from Step 3.

## Step 6: Update Your `.env` File

You will need to add these new credentials to your `.env` file so our application can use them. The application will need keys for the Backblaze S3-compatible API.

Please follow these instructions carefully. Once you have completed these steps, let me know, and I will proceed with the code implementation.
