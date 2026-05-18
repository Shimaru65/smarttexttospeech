"""
SmartTextToSpeech — Desktop Entry Point
Starts Flask in background, opens browser, shows system tray icon.
"""
import sys
import os
import socket
import threading
import webbrowser
import time
from pathlib import Path


# ── Path helpers ──────────────────────────────────────────────────────────────

def resource_path(rel: str) -> Path:
    """Resolve path whether running as script or frozen .exe (PyInstaller)."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / rel


def get_audio_dir() -> Path:
    """Store generated audio in AppData — always writable, survives updates."""
    appdata = Path(os.environ.get('APPDATA', '')) or Path.home()
    d = appdata / 'SmartTextToSpeech' / 'audio'
    d.mkdir(parents=True, exist_ok=True)
    return d


def find_free_port(start: int = 5000) -> int:
    """Find first available TCP port starting from `start`."""
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return start


def wait_for_server(port: int, timeout: int = 20) -> bool:
    """Block until Flask is accepting connections or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) == 0:
                return True
        time.sleep(0.3)
    return False


# ── Tray icon ─────────────────────────────────────────────────────────────────

def make_icon_image():
    from PIL import Image, ImageDraw
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Purple circle background
    d.ellipse([2, 2, 62, 62], fill=(124, 58, 237, 255))
    # Microphone body
    d.rounded_rectangle([24, 12, 40, 36], radius=8, fill=(255, 255, 255, 255))
    # Microphone stand
    d.rectangle([30, 36, 34, 48], fill=(255, 255, 255, 255))
    # Microphone base arc (approximated with ellipse)
    d.arc([20, 42, 44, 56], start=180, end=0, fill=(255, 255, 255, 255), width=3)
    d.rectangle([30, 54, 34, 58], fill=(255, 255, 255, 255))
    return img


def show_error(msg: str):
    """Show a simple error dialog without requiring any extra package."""
    try:
        import tkinter
        import tkinter.messagebox
        root = tkinter.Tk()
        root.withdraw()
        tkinter.messagebox.showerror('SmartTextToSpeech — Error', msg)
        root.destroy()
    except Exception:
        pass  # Silent if tkinter unavailable


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    port = find_free_port(5000)
    url  = f'http://localhost:{port}'

    # Pass config to app.py via environment (before importing Flask app)
    os.environ['TTS_TEMPLATE_FOLDER'] = str(resource_path('templates'))
    os.environ['TTS_STATIC_FOLDER']   = str(resource_path('static'))
    os.environ['TTS_AUDIO_DIR']       = str(get_audio_dir())
    os.environ['TTS_PORT']            = str(port)

    # Start Flask in a daemon thread
    flask_ok = threading.Event()
    flask_err: list[str] = []

    def run_flask():
        try:
            from app import app
            flask_ok.set()
            app.run(host='127.0.0.1', port=port,
                    debug=False, use_reloader=False, threaded=True)
        except Exception as exc:
            flask_err.append(str(exc))
            flask_ok.set()

    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # Wait until Flask is ready (or fails)
    if not wait_for_server(port, timeout=20):
        msg = flask_err[0] if flask_err else 'Flask did not start within 20 seconds.'
        show_error(msg)
        sys.exit(1)

    # Open browser
    webbrowser.open(url)

    # System tray icon
    try:
        import pystray

        def on_open(icon, item):
            webbrowser.open(url)

        def on_quit(icon, item):
            icon.stop()
            sys.exit(0)

        tray = pystray.Icon(
            name='SmartTextToSpeech',
            icon=make_icon_image(),
            title='SmartTextToSpeech',
            menu=pystray.Menu(
                pystray.MenuItem('เปิดแอป / Open App', on_open, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem('ปิดโปรแกรม / Quit', on_quit),
            ),
        )
        tray.run()

    except Exception:
        # Fallback: keep alive without tray icon
        t.join()


if __name__ == '__main__':
    main()
