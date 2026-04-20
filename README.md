# 🤖 Raspberry Pi 5 — Local AI Voice Assistant

**Ubuntu 24.04 + Bluetooth Earbuds + Ollama + Whisper + Piper**

A fully offline voice chat assistant running on a Raspberry Pi 5. No cloud. No API keys. No wires for audio. Just a Pi, a pair of Bluetooth earbuds, and some patience.

> 📖 **Read the full story behind this project on Medium:** [YOUR_MEDIUM_ARTICLE_LINK]

---

## Demo

![System booting up](https://raw.githubusercontent.com/pradhangagan/chatbot-v1/main/image%20and%20video/IMG_5549.jpg)
*System startup — Whisper loading, earbuds visible in frame*

![Whisper model loading](https://raw.githubusercontent.com/pradhangagan/chatbot-v1/main/image%20and%20video/IMG_5550.jpg)
*Whisper model parameters initializing on first run*

![Full pipeline working](https://raw.githubusercontent.com/pradhangagan/chatbot-v1/main/image%20and%20video/WhatsApp%20Image%202026-04-20%20at%203.30.09%20PM.jpeg)
*"What is the capital of Australia?" — transcribed, answered, spoken back through earbuds*

🎬 **[Watch the full demo video](https://github.com/pradhangagan/chatbot-v1/raw/main/image%20and%20video/WhatsApp%20Video%202026-04-20%20at%203.29.46%20PM.mp4)**

---

## What This Is

This repo contains everything you need to build a fully local voice assistant on a Raspberry Pi 5 using Bluetooth earbuds as both mic and speaker:

- You **speak** into Bluetooth earbuds → **Whisper.cpp** transcribes on-device
- **Ollama** runs a local LLM (llama3.2:3b) to generate a response
- **Piper TTS** converts the response to speech and plays back through your earbuds

---

## Repo Structure

```
📄 RaspberryPi5_Ubuntu_BT_Earbuds_Guide.docx   ← Full step-by-step setup guide
🐍 robot_ubuntu_bt.py                           ← Main assistant script (full pipeline)
🐍 test_stt_bt.py                               ← Test Whisper STT via BT mic
🐍 test_tts_bt.py                               ← Test Piper TTS via BT speaker
📁 assets/                                      ← Images and demo video
```

### File descriptions

**`robot_ubuntu_bt.py`** — The main script. Press Enter to start speaking, press Enter again to stop. Whisper transcribes → Ollama thinks → Piper speaks the answer back through your earbuds. Runs in a loop until you hit Ctrl+C.

**`test_stt_bt.py`** — Standalone test for speech-to-text only. Records 5 seconds from your BT mic and prints the Whisper transcription. Good for checking if your mic and Whisper are working before running the full pipeline.

**`test_tts_bt.py`** — Standalone test for text-to-speech only. Generates a sample sentence with Piper and plays it through your BT earbuds via `paplay`. Good for verifying audio output works.

**`RaspberryPi5_Ubuntu_BT_Earbuds_Guide.docx`** — The complete written guide covering all 7 parts: Ubuntu setup, PipeWire, Ollama, Bluetooth pairing + HFP profile, Whisper STT, Piper TTS, and the full pipeline. Download this if you want the full reference offline.

---

## Stack

| Component | Purpose | Model/Version |
|-----------|---------|---------------|
| [Ollama](https://ollama.com) | Local LLM inference | llama3.2:3b |
| [whisper.cpp](https://github.com/ggerganov/whisper.cpp) + pywhispercpp | Speech-to-text | base.en |
| [Piper TTS](https://github.com/rhasspy/piper) | Text-to-speech | en_US-lessac-medium |
| PipeWire + WirePlumber | Bluetooth audio stack | Ubuntu default |
| Ubuntu 24.04 LTS (64-bit ARM) | OS | — |

---

## Hardware

- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- Bluetooth earbuds (any HFP-capable pair)
- MicroSD card (32GB+ recommended)
- Optional: small touchscreen display

---

## Honest Performance Notes

Before you start, know what you're getting into:

- **Inference speed:** Simple questions take 15–30 seconds. Complex questions can take 60–120 seconds. The default timeout in the script is set to 120s — don't lower it or you'll get timeout errors on longer responses.
- **Transcription accuracy:** Whisper `base.en` works well for clear speech in a quiet room. HFP Bluetooth audio is compressed (16kHz mono), which affects accuracy. Upgrading to `small.en` helps.
- **Audio quality:** HFP mode sounds like a phone call. This is expected — it's the trade-off for enabling the microphone over Bluetooth.

---

## Quick Start

### 1 — System prep & PipeWire

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential python3 python3-pip python3-venv

sudo apt install -y pipewire pipewire-pulse pipewire-alsa pipewire-jack \
    wireplumber libspa-0.2-bluetooth bluez bluez-tools \
    pavucontrol pulseaudio-utils

# Do NOT use sudo for these
systemctl --user enable pipewire pipewire-pulse wireplumber
systemctl --user start pipewire pipewire-pulse wireplumber

# Verify
pactl info | grep 'Server Name'
# Expected: Server Name: PulseAudio (on PipeWire x.x.x)
```

### 2 — Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

### 3 — Pair Bluetooth Earbuds & Switch to HFP

```bash
bluetoothctl
# Inside the prompt:
power on
agent on
default-agent
scan on
# Wait for your earbuds to appear, then:
pair   AA:BB:CC:DD:EE:FF
trust  AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
exit

# Switch to HFP profile — this enables the microphone
pactl list cards | grep -E 'Name:|bluez'
pactl set-card-profile bluez_card.AA_BB_CC_DD_EE_FF headset-head-unit
```

**Make HFP persist across reboots:**

```bash
mkdir -p ~/.config/pipewire/pipewire-pulse.conf.d
cat > ~/.config/pipewire/pipewire-pulse.conf.d/99-bt-headset.conf << 'EOF'
pulse.cmd = [
  { cmd = "load-module" args = "module-bluetooth-policy auto_switch=2" }
]
EOF

systemctl --user restart pipewire pipewire-pulse wireplumber
```

### 4 — Build Whisper.cpp

```bash
sudo apt install -y build-essential cmake libsdl2-dev libportaudio2 portaudio19-dev
cd ~
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
bash ./models/download-ggml-model.sh base.en
```

### 5 — Python environment

```bash
cd ~
python3 -m venv robot-env
source robot-env/bin/activate
pip install pywhispercpp sounddevice soundfile numpy piper-tts requests
```

### 6 — Download Piper voice

```bash
mkdir -p ~/piper-voices && cd ~/piper-voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### 7 — Clone this repo and run

```bash
git clone https://github.com/pradhangagan/pi5-voice-assistant
cd pi5-voice-assistant
source ~/robot-env/bin/activate
python3 robot_ubuntu_bt.py
```

> 💡 For the full guide with every step, error fix, and explanation — download **`RaspberryPi5_Ubuntu_BT_Earbuds_Guide.docx`** from this repo.

---

## Testing Individual Components

Before running the full pipeline, test each piece separately:

```bash
# Test microphone + Whisper transcription
python3 test_stt_bt.py

# Test Piper TTS + BT speaker
python3 test_tts_bt.py

# Then run the full assistant
python3 robot_ubuntu_bt.py
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Mic not appearing as audio source | Switch to HFP: `pactl set-card-profile bluez_card.XX headset-head-unit` |
| `headset-head-unit` not found | Try `hsp_hs` or `hfp_hf`. List all profiles: `pactl list cards \| grep -A 20 bluez` |
| Earbuds reconnect in A2DP after reboot | Check the PipeWire config from Step 3 is saved correctly |
| `paplay` not found / connection refused | `systemctl --user start pipewire-pulse` |
| Ollama timeout on complex questions | Timeout is already 120s in the script. Switch to `gemma2:2b` for faster responses |
| Whisper transcription garbled | Confirm HFP mode is active. Try `small.en` model. Quieter room helps. |
| `sounddevice` import error | `sudo apt install -y libportaudio2 portaudio19-dev` |

---

## Planned Upgrades

- [ ] Wake word detection (openWakeWord) — no more pressing Enter
- [ ] Streaming TTS — speak first sentence while rest is still generating
- [ ] USB microphone support for better transcription accuracy
- [ ] Model comparison: gemma2:2b vs llama3.2:1b for voice use case

---

## License

MIT — do whatever you want with it.

---

*Built by [@pradhangagan](https://github.com/pradhangagan) · Raspberry Pi 5 · Ubuntu 24.04 LTS · April 2026*
