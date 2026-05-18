from flask import Flask, request, jsonify, send_file, render_template
import edge_tts
import asyncio
import concurrent.futures
import os
import uuid
import threading
import time
from pathlib import Path


def run_in_new_loop(coro):
    """Run an async coroutine in a brand-new thread+event-loop (avoids Windows asyncio conflicts inside Flask)."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result(timeout=60)


# When running as a frozen .exe (via main.py), paths are injected via env vars.
# When running as a plain script, fall back to the file's own directory.
_base = Path(__file__).parent
_tmpl   = os.environ.get('TTS_TEMPLATE_FOLDER') or str(_base / 'templates')
_static = os.environ.get('TTS_STATIC_FOLDER')   or str(_base / 'static')
_audio  = os.environ.get('TTS_AUDIO_DIR')        or str(_base / 'audio')

app = Flask(__name__, template_folder=_tmpl, static_folder=_static)

BASE_DIR  = _base
AUDIO_DIR = Path(_audio)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

LANGUAGES = {
    "th-TH": {
        "name": "ภาษาไทย (Thai)",
        "flag": "🇹🇭",
        "voices": [
            {"id": "th-TH-PremwadeeNeural", "name": "Premwadee", "gender": "female", "display": "พรวดี (หญิง)"},
            {"id": "th-TH-AcharaNeural",    "name": "Achara",    "gender": "female", "display": "อาจารา (หญิง)"},
            {"id": "th-TH-NiwatNeural",     "name": "Niwat",     "gender": "male",   "display": "นิวัฒน์ (ชาย)"},
        ],
    },
    "en-US": {
        "name": "English (US)",
        "flag": "🇺🇸",
        "voices": [
            {"id": "en-US-JennyNeural", "name": "Jenny", "gender": "female", "display": "Jenny (Female)"},
            {"id": "en-US-AriaNeural",  "name": "Aria",  "gender": "female", "display": "Aria (Female)"},
            {"id": "en-US-GuyNeural",   "name": "Guy",   "gender": "male",   "display": "Guy (Male)"},
            {"id": "en-US-DavisNeural", "name": "Davis", "gender": "male",   "display": "Davis (Male)"},
        ],
    },
    "en-GB": {
        "name": "English (UK)",
        "flag": "🇬🇧",
        "voices": [
            {"id": "en-GB-SoniaNeural", "name": "Sonia", "gender": "female", "display": "Sonia (Female)"},
            {"id": "en-GB-RyanNeural",  "name": "Ryan",  "gender": "male",   "display": "Ryan (Male)"},
        ],
    },
    "zh-CN": {
        "name": "中文 (Chinese)",
        "flag": "🇨🇳",
        "voices": [
            {"id": "zh-CN-XiaoxiaoNeural", "name": "Xiaoxiao", "gender": "female", "display": "晓晓 (女)"},
            {"id": "zh-CN-XiaoyiNeural",   "name": "Xiaoyi",   "gender": "female", "display": "晓伊 (女)"},
            {"id": "zh-CN-YunxiNeural",    "name": "Yunxi",    "gender": "male",   "display": "云希 (男)"},
        ],
    },
    "ja-JP": {
        "name": "日本語 (Japanese)",
        "flag": "🇯🇵",
        "voices": [
            {"id": "ja-JP-NanamiNeural", "name": "Nanami", "gender": "female", "display": "七海 (女)"},
            {"id": "ja-JP-KeitaNeural",  "name": "Keita",  "gender": "male",   "display": "敬太 (男)"},
        ],
    },
}

SAFE_FILENAME = set("abcdefghijklmnopqrstuvwxyz0123456789-.")


def _is_safe_filename(name: str) -> bool:
    return bool(name) and name.endswith(".mp3") and all(c in SAFE_FILENAME for c in name)


def _cleanup_worker():
    while True:
        try:
            cutoff = time.time() - 3600
            for f in AUDIO_DIR.glob("*.mp3"):
                if f.stat().st_mtime < cutoff:
                    f.unlink(missing_ok=True)
        except Exception:
            pass
        time.sleep(300)


threading.Thread(target=_cleanup_worker, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/languages")
def get_languages():
    return jsonify(LANGUAGES)


@app.route("/api/generate", methods=["POST"])
def generate_speech():
    try:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()
        voice = data.get("voice", "th-TH-PremwadeeNeural")
        rate = max(-50, min(50, int(data.get("rate", 0))))
        pitch = max(-50, min(50, int(data.get("pitch", 0))))

        if not text:
            return jsonify({"error": "กรุณาใส่ข้อความ (Please enter text)"}), 400
        if len(text) > 5000:
            return jsonify({"error": "ข้อความยาวเกินไป — สูงสุด 5,000 ตัวอักษร"}), 400

        rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
        pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"{pitch}Hz"

        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = AUDIO_DIR / filename

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate_str, pitch=pitch_str)
            await communicate.save(str(filepath))

        run_in_new_loop(_generate())

        if not filepath.exists() or filepath.stat().st_size == 0:
            return jsonify({"error": "ไม่สามารถสร้างไฟล์เสียงได้ (Failed to generate audio)"}), 500

        return jsonify({
            "success": True,
            "filename": filename,
            "url": f"/api/audio/{filename}",
            "download_url": f"/api/download/{filename}",
            "file_size": filepath.stat().st_size,
        })

    except edge_tts.exceptions.NoAudioReceived:
        return jsonify({"error": "ไม่ได้รับข้อมูลเสียง — ลองข้อความอื่น (No audio received)"}), 500
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/audio/<filename>")
def stream_audio(filename):
    if not _is_safe_filename(filename):
        return jsonify({"error": "Invalid filename"}), 400
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(str(filepath), mimetype="audio/mpeg")


@app.route("/api/download/<filename>")
def download_audio(filename):
    if not _is_safe_filename(filename):
        return jsonify({"error": "Invalid filename"}), 400
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "File not found"}), 404
    return send_file(
        str(filepath),
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="speech.mp3",
    )


if __name__ == "__main__":
    print("\n" + "=" * 54)
    print("  SmartTextToSpeech — Thai TTS Application")
    print("  Open: http://localhost:5000")
    print("=" * 54 + "\n")
    app.run(debug=False, port=5000, host="0.0.0.0")
