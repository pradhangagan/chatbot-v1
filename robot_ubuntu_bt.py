import sounddevice as sd
import numpy as np
import subprocess
import requests
import os
import sys
import select
import threading
from pywhispercpp.model import Model

# --- CONFIGURATION ---
WHISPER_MODEL = os.path.expanduser('~/whisper.cpp/models/ggml-base.en.bin')
PIPER_MODEL   = os.path.expanduser('~/piper-voices/en_US-lessac-medium.onnx')
OLLAMA_URL    = 'http://localhost:11434/api/generate'
LLM_MODEL     = 'llama3.2:3b'  # Fast and smart for Pi 5
SAMPLE_RATE   = 16000          # Native Bluetooth HFP rate

# --- INITIALIZATION ---
print("\n[1/3] Loading Whisper (Ears)...")
stt = Model(WHISPER_MODEL)

print("[2/3] Checking Ollama (Brain)...")
# Note: Ensure 'ollama serve' is running in another terminal!

print("[3/3] System Calibration Complete.")

def flush_input():
    """Clears the terminal's keyboard buffer to prevent 'ghost' recordings."""
    try:
        while select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.read(1)
    except:
        pass

def speak(text):
    """Generates speech via Piper CLI and plays via paplay."""
    print(f'Robot: {text}')
    output_file = "/tmp/reply.wav"
    # Remove single quotes to prevent shell command errors
    safe_text = text.replace("'", "")
    
    # We use the CLI version of Piper as it is most robust on Pi 5
    cmd = f"echo '{safe_text}' | piper --model {PIPER_MODEL} --output-file {output_file}"
    subprocess.run(cmd, shell=True, check=True)
    subprocess.run(['paplay', output_file], check=True)

def ask_llm(prompt):
    """Sends text to Ollama and returns the response."""
    try:
        res = requests.post(OLLAMA_URL,
            json={'model': LLM_MODEL, 'prompt': prompt, 'stream': False},
            timeout=120)
        return res.json()['response'].strip()
    except Exception as e:
        return f"Brain error: {e}"

def record_dynamic_audio():
    """Records audio from the moment Enter is pressed until it is pressed again."""
    recorded_chunks = []
    stop_event = threading.Event()

    def callback(indata, frames, time, status):
        if not stop_event.is_set():
            recorded_chunks.append(indata.copy())

    print("\n>>> RECORDING... Press [ENTER] again to stop.")
    
    # Start the stream
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=callback, dtype='float32'):
        input() # Wait for the second Enter
        stop_event.set()

    return np.concatenate(recorded_chunks)

# --- MASTER LOOP ---
def main():
    speak("System online, Gagan. All systems nominal.")

    while True:
        try:
            print("\n" + "="*40)
            print("STATUS: Idle")
            flush_input() # Clean out any accidental keypresses
            
            input("ACTION: Press [ENTER] to start speaking...")
            
            # 1. Record
            audio_data = record_dynamic_audio()
            
            if len(audio_data) < SAMPLE_RATE * 0.5:
                print("Too short! Try again.")
                continue

            # 2. Transcribe
            print("STATUS: Transcribing (Ears)...")
            segments = stt.transcribe(audio_data.flatten())
            question = ' '.join([s.text for s in segments]).strip()
            
            if not question or len(question) < 2:
                print("No speech detected.")
                continue
                
            print(f"YOU: {question}")

            # 3. Think
            print(f"STATUS: Thinking ({LLM_MODEL})...")
            answer = ask_llm(question)
            
            # 4. Speak
            speak(answer)

        except KeyboardInterrupt:
            print("\nShutting down assistant...")
            break
        except Exception as e:
            print(f"\nSystem Error: {e}")

if __name__ == "__main__":
    main()
