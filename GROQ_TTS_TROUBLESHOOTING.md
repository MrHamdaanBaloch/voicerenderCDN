# Groq TTS API Troubleshooting Guide

## Issue Summary
Your application is experiencing a `400 Bad Request` error from the Groq Text-to-Speech API with the error code `model_terms_required`. This means the `playai-tts` model requires terms acceptance before it can be used.

## Error Details
```
WARNING:root:[call-id] Groq TTS failed with status 400: {
  "error": {
    "message": "The model playai-tts requires terms acceptance. Please have the org admin accept the terms at https://console.groq.com/playground?model=playai-tts",
    "type": "invalid_request_error",
    "code": "model_terms_required"
  }
}
```

## ✅ Solution Steps

### 1. Accept Model Terms (Required)
1. **Visit the Groq Console**: https://console.groq.com/playground?model=playai-tts
2. **Login** with your Groq account (the one associated with your API key)
3. **Accept the terms** for the `playai-tts` model
4. **Wait 2-5 minutes** for the changes to propagate through Groq's systems

### 2. Verify the Fix
Run the diagnostic tool to check if the issue is resolved:

```bash
cd AIVOICE
python utils/groq_tts_checker.py
```

This tool will:
- ✅ Test if the `playai-tts` model is working
- 📋 List all available TTS models
- 🎭 Test different voice options
- 💡 Provide specific recommendations

### 3. Alternative Solutions (If Terms Can't Be Accepted)

If you cannot accept the terms immediately, you have several options:

#### Option A: Use Different Groq Model
Update your `relay_server.py` to use an alternative model:

```python
payload = {
    "model": "whisper-large-v3-turbo",  # Alternative model
    "voice": "alloy",
    "input": text,
    "response_format": "wav"
}
```

#### Option B: Rely on SignalWire Fallback
Your application already has a robust fallback system. SignalWire TTS will be used automatically when Groq fails, ensuring uninterrupted service.

#### Option C: Disable Groq TTS Temporarily
Add an environment variable to temporarily disable Groq TTS:

```bash
# In your .env file
DISABLE_GROQ_TTS=true
```

Then update your code to check this flag before attempting Groq TTS.

## 🔧 What We've Fixed

### 1. Enhanced Error Handling
- ✅ Better error parsing and logging
- ✅ Specific detection of `model_terms_required` errors
- ✅ Clear instructions in logs when terms need acceptance

### 2. Improved Fallback Logic
- ✅ Graceful fallback to SignalWire TTS
- ✅ Performance timing for both primary and fallback TTS
- ✅ Multiple fallback layers for maximum reliability

### 3. Diagnostic Tools
- ✅ Created `groq_tts_checker.py` for troubleshooting
- ✅ Model availability testing
- ✅ Voice option testing
- ✅ Comprehensive error reporting

## 🚀 Current System Behavior

Your application now handles the Groq TTS issue gracefully:

1. **Attempts Groq TTS** first (fastest, highest quality)
2. **Detects terms requirement** and logs clear instructions
3. **Falls back to SignalWire TTS** automatically (reliable backup)
4. **Continues normal operation** without user-facing errors

## 📊 Performance Impact

- **With Groq TTS**: ~1-2 seconds response time
- **With SignalWire Fallback**: ~2-3 seconds response time
- **User Experience**: Minimal impact, seamless operation

## 🔍 Monitoring & Logs

Watch for these log messages:

### ✅ Success Messages
```
[call-id] Groq TTS successful! Total time: 1.23s
[call-id] SignalWire TTS successful! Time: 2.45s
```

### ⚠️ Warning Messages
```
[call-id] Groq TTS model terms not accepted. Please visit: https://console.groq.com/playground?model=playai-tts
[call-id] Using SignalWire TTS fallback
```

### ❌ Error Messages (Rare)
```
[call-id] SignalWire TTS failed: [reason]
[call-id] Emergency fallback also failed: [reason]
```

## 🛠️ Testing Your Fix

### Quick Test
```bash
# Run the diagnostic tool
python utils/groq_tts_checker.py
```

### Full Integration Test
1. Start your application
2. Make a test call
3. Check logs for TTS behavior
4. Verify audio quality and response times

## 📞 Support

If you continue experiencing issues after accepting the terms:

1. **Check API Key**: Ensure your `GROQ_API_KEY` is correct
2. **Check Account Status**: Verify your Groq account is in good standing
3. **Check Rate Limits**: Ensure you haven't exceeded API quotas
4. **Contact Groq Support**: If the issue persists after accepting terms

## 🎯 Next Steps

1. ✅ Accept the model terms at https://console.groq.com/playground?model=playai-tts
2. ✅ Run the diagnostic tool to verify
3. ✅ Monitor your application logs
4. ✅ Enjoy improved TTS performance!

---

**Note**: Your application will continue working normally with SignalWire TTS fallback even if Groq TTS remains unavailable. The user experience remains seamless throughout this process.
