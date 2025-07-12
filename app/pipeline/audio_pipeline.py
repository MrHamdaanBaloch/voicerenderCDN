# app/pipeline/audio_pipeline.py

def run_full_pipeline_from_file(input_audio_path: str) -> str:
    """Run STT → LLM → TTS pipeline. Returns output .wav path."""
    if not os.path.exists(input_audio_path):
        raise FileNotFoundError(f"Input audio file '{input_audio_path}' not found.")
    
    # Step 1: Load Audio
    with wave.open(input_audio_path, 'rb') as wf:
        num_channels, sample_width_bytes, original_sr, num_frames, _, _ = wf.getparams()
        audio_frames_bytes = wf.readframes(num_frames)
    
    pcm_s16_original_sr = np.frombuffer(audio_frames_bytes, dtype=np.int16)
    if num_channels > 1:
        pcm_s16_original_sr = pcm_s16_original_sr.reshape(-1, num_channels).mean(axis=1).astype(np.int16)
    
    pcm_f32_original_sr = pcm_s16_to_float32(pcm_s16_original_sr)
    pcm_f32_stt_sr = resample_audio(pcm_f32_original_sr, original_sr, TARGET_STT_SAMPLE_RATE)

    # Step 2: STT
    segments, _ = stt_model.transcribe(pcm_f32_stt_sr, beam_size=5, language="en")
    transcribed_text = "".join(segment.text for segment in segments).strip()

    # Step 3: LLM
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You are a concise AI assistant."},
            {"role": "user", "content": transcribed_text}
        ],
        model=LLM_MODEL,
        max_tokens=60
    )
    llm_response_text = chat_completion.choices[0].message.content.strip()

    # Step 4: TTS
    raw_audio_bytes = bytearray(b''.join(piper_voice.synthesize_stream_raw(llm_response_text)))

    output_path = "output_tts_response.wav"
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(piper_native_sample_rate)
        wf.writeframes(bytes(raw_audio_bytes))

    return output_path
