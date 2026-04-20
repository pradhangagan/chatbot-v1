import subprocess
import os

# Path to your voice model
VOICE_MODEL = os.path.expanduser('~/piper-voices/en_US-lessac-medium.onnx')

def speak(text):
    print(f'Speaking: {text}')
    
    # 1. Generate the WAV file using the Piper CLI (which handles headers correctly)
    # We use a temporary file path
    output_file = "/tmp/speech.wav"
    
    # This mirrors the command that worked in your terminal
    # We use 'shell=True' so we can use the pipe (|)
    cmd = f"echo '{text}' | piper --model {VOICE_MODEL} --output-file {output_file}"
    
    # Run the generation
    subprocess.run(cmd, shell=True, check=True)
    
    # 2. Play it through your Bluetooth earbuds using paplay
    subprocess.run(['paplay', output_file], check=True)

if __name__ == "__main__":
    speak('The system is fully operational. All audio plumbing is now correct.')
