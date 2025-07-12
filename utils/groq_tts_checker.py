#!/usr/bin/env python3
"""
Groq TTS Model Checker and Fallback Manager
This utility helps diagnose and manage Groq TTS API issues.
"""

import os
import asyncio
import aiohttp
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqTTSChecker:
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1"
        
    async def check_model_availability(self, model_name: str = "playai-tts"):
        """Check if a specific TTS model is available and terms are accepted"""
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test payload
        payload = {
            "model": model_name,
            "voice": "Fritz-PlayAI",
            "input": "Test message",
            "response_format": "wav"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.post(
                    f"{self.base_url}/audio/speech",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"✅ Model '{model_name}' is available and working!")
                        return True
                    else:
                        error_content = await resp.text()
                        try:
                            error_data = json.loads(error_content)
                            error_code = error_data.get('error', {}).get('code', 'unknown')
                            error_message = error_data.get('error', {}).get('message', 'Unknown error')
                            
                            if error_code == 'model_terms_required':
                                logger.warning(f"❌ Model '{model_name}' requires terms acceptance!")
                                logger.warning(f"📋 Please visit: https://console.groq.com/playground?model={model_name}")
                                logger.warning("👤 Have your organization admin accept the terms.")
                            else:
                                logger.error(f"❌ Model '{model_name}' failed: {error_message} (Code: {error_code})")
                                
                        except json.JSONDecodeError:
                            logger.error(f"❌ Model '{model_name}' failed with status {resp.status}: {error_content}")
                        
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Error checking model '{model_name}': {e}")
            return False
    
    async def list_available_models(self):
        """List all available models from Groq API"""
        if not self.api_key:
            logger.error("GROQ_API_KEY not found in environment variables")
            return []
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = data.get('data', [])
                        
                        # Filter for TTS models
                        tts_models = [model for model in models if 'tts' in model.get('id', '').lower()]
                        
                        logger.info("🎤 Available TTS Models:")
                        for model in tts_models:
                            logger.info(f"  - {model.get('id', 'Unknown')}")
                            
                        return tts_models
                    else:
                        error_content = await resp.text()
                        logger.error(f"❌ Failed to list models: {error_content}")
                        return []
                        
        except Exception as e:
            logger.error(f"❌ Error listing models: {e}")
            return []
    
    async def test_alternative_voices(self, model_name: str = "playai-tts"):
        """Test different voice options for a model"""
        voices = [
            "Fritz-PlayAI",
            "Aria-PlayAI", 
            "Nova-PlayAI",
            "Alloy-PlayAI",
            "Echo-PlayAI",
            "Fable-PlayAI",
            "Onyx-PlayAI",
            "Shimmer-PlayAI"
        ]
        
        logger.info(f"🎭 Testing voices for model '{model_name}'...")
        
        working_voices = []
        for voice in voices:
            success = await self._test_voice(model_name, voice)
            if success:
                working_voices.append(voice)
                
        if working_voices:
            logger.info(f"✅ Working voices: {', '.join(working_voices)}")
        else:
            logger.warning("❌ No working voices found")
            
        return working_voices
    
    async def _test_voice(self, model_name: str, voice: str):
        """Test a specific voice"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_name,
            "voice": voice,
            "input": "Test",
            "response_format": "wav"
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(
                    f"{self.base_url}/audio/speech",
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"  ✅ Voice '{voice}' works")
                        return True
                    else:
                        logger.info(f"  ❌ Voice '{voice}' failed (status: {resp.status})")
                        return False
                        
        except Exception as e:
            logger.info(f"  ❌ Voice '{voice}' error: {e}")
            return False

async def main():
    """Main diagnostic function"""
    print("🔍 Groq TTS Diagnostic Tool")
    print("=" * 40)
    
    checker = GroqTTSChecker()
    
    # Check primary model
    print("\n1. Checking primary model (playai-tts)...")
    primary_available = await checker.check_model_availability("playai-tts")
    
    # List all available models
    print("\n2. Listing all available models...")
    await checker.list_available_models()
    
    # Test alternative voices if primary model has terms issues
    if not primary_available:
        print("\n3. Testing alternative voices (if terms are accepted)...")
        await checker.test_alternative_voices("playai-tts")
    
    print("\n" + "=" * 40)
    print("🎯 RECOMMENDATIONS:")
    
    if primary_available:
        print("✅ Your Groq TTS setup is working correctly!")
    else:
        print("❌ Action required:")
        print("   1. Visit https://console.groq.com/playground?model=playai-tts")
        print("   2. Have your organization admin accept the model terms")
        print("   3. Wait a few minutes for changes to propagate")
        print("   4. Re-run this diagnostic tool")
        print("\n💡 In the meantime, your app will use SignalWire TTS as fallback")

if __name__ == "__main__":
    asyncio.run(main())
