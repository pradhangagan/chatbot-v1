import sounddevice as sd
import numpy as np
from pywhispercpp.model import Model
import os

MODEL_PATH = os.path.expanduser('~/whisper.cpp/models/ggml-base.en.bin')
DURATION    = 5       # seconds
SAMPLE_RATE = 16000   # HFP BT mic native rate — no resampling needed

print('Loading Whisper model...')
model = Model(MODEL_PATH)

# List available input devices so you can confirm BT mic is selected
print('\nAvailable audio input devices:')
print(sd.query_devices())
print(f'\nDefault input: {sd.query_devices(kind="input")["name"]}')

input('\nPress Enter to record 5 seconds — speak into your earbuds...')
audio = sd.rec(int(DURATION * SAMPLE_RATE),
               samplerate=SAMPLE_RATE, channels=1, dtype='float32')
sd.wait()
print('Transcribing...')
segments = model.transcribe(audio.flatten())
text = ' '.join([s.text for s in segments]).strip()
print(f'You said: {text}')
