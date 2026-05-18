# SmartTextToSpeech 🎙️

A free, locally-hosted Text-to-Speech web application with excellent Thai language support.
Powered by **Microsoft Edge TTS** (via `edge-tts`) + **Flask** — no API keys, no subscriptions, no cloud dependency.

---

## Features

- **Thai language TTS** — 3 high-quality neural voices (2 female, 1 male)
- **5 languages** — Thai, English (US/UK), Chinese, Japanese
- **Adjustable speed** — ±50% from normal
- **Adjustable pitch** — ±50 Hz from normal
- **Download as MP3** — save files directly to your computer
- **Dark/Light mode** toggle
- **Mobile-responsive** design
- Character count, word count, file-size stats

---

## Requirements

- Python 3.10 or newer
- Internet connection (Edge TTS fetches audio from Microsoft's servers)

---

## Installation

### 1. Clone / download the project

Place the project folder wherever you like (e.g. `C:\xampp\htdocs\smarttexttospeech`).

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

Packages installed:
| Package | Purpose |
|---------|---------|
| `flask` | Web server / API |
| `edge-tts` | Microsoft Edge neural TTS engine |

### 3. Run the application

```bash
python app.py
```

You should see:

```
══════════════════════════════════════════════════════
  SmartTextToSpeech — Thai TTS Application
  Open: http://localhost:5000
══════════════════════════════════════════════════════
```

### 4. Open in browser

Navigate to **http://localhost:5000**

---

## Project Structure

```
smarttexttospeech/
├── app.py                  # Flask backend + API routes
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Main HTML page
├── static/
│   ├── css/style.css       # Styles (dark/light mode, responsive)
│   └── js/app.js           # Frontend logic
├── audio/                  # Generated MP3 files (auto-cleaned hourly)
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main web interface |
| `GET` | `/api/languages` | List all languages and voices |
| `POST` | `/api/generate` | Generate TTS audio |
| `GET` | `/api/audio/<filename>` | Stream audio for playback |
| `GET` | `/api/download/<filename>` | Download MP3 |

### POST `/api/generate`

```json
{
  "text": "สวัสดีครับ",
  "voice": "th-TH-PremwadeeNeural",
  "rate": 0,
  "pitch": 0
}
```

| Field | Type | Range | Default |
|-------|------|-------|---------|
| `text` | string | 1–5000 chars | — |
| `voice` | string | see `/api/languages` | `th-TH-PremwadeeNeural` |
| `rate` | int | -50 to +50 | `0` |
| `pitch` | int | -50 to +50 | `0` |

---

## Available Thai Voices

| Voice ID | Name | Gender |
|----------|------|--------|
| `th-TH-PremwadeeNeural` | Premwadee (พรวดี) | Female |
| `th-TH-AcharaNeural` | Achara (อาจารา) | Female |
| `th-TH-NiwatNeural` | Niwat (นิวัฒน์) | Male |

---

## Notes

- Generated audio files are automatically deleted after **1 hour**.
- Maximum input text: **5,000 characters** per request.
- The app uses `edge-tts` which connects to Microsoft's Edge TTS service — a free internet connection is required.
- No data is stored permanently; audio files are temporary.

---

## Troubleshooting

**"No audio received" error**  
→ Check your internet connection. Edge TTS requires access to Microsoft's servers.

**Port 5000 already in use**  
→ Change the port in `app.py`: `app.run(port=5001)`

**Thai characters not displaying correctly**  
→ Ensure your browser supports UTF-8 (all modern browsers do).
