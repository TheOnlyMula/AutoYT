import wave
import numpy as np
from kokoro import KPipeline

import utils.format as format

SAMPLE_RATE = 24000  # Kokoro outputs 24 kHz audio

def generate_tts_wav(text, voice, speed):
    text = format.format_text(text)
    pipeline = KPipeline(lang_code = voice[0], repo_id = "hexgrad/Kokoro-82M")

    chunks, words = [], []
    offset = 0.0
    for result in pipeline(text, voice = voice, speed = speed):
        for token in result.tokens:
            if token.start_ts is None or token.end_ts is None:
                continue
            start, end = offset + token.start_ts, offset + token.end_ts
            if words and not any(c.isalnum() for c in token.text):
                word, word_start, _ = words[-1]
                words[-1] = (word + token.text, word_start, end)
            else:
                words.append((token.text, start, end))

        chunks.append(result.audio)
        offset += len(result.audio) / SAMPLE_RATE

    audio = np.concatenate(chunks)
    return audio, words

def write_wav(path, audio): 
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w: 
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())