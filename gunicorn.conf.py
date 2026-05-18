# Gunicorn configuration — used on Linux production servers
# Run with: gunicorn --config gunicorn.conf.py wsgi:app

bind             = "127.0.0.1:5000"
workers          = 2          # Keep low: each worker spawns a thread for edge-tts
worker_class     = "sync"
timeout          = 120        # TTS generation can take up to 30s on slow connections
keepalive        = 5
max_requests     = 500        # Recycle workers to prevent memory bloat
max_requests_jitter = 50

# Logging — adjust paths to match your server setup
accesslog = "/var/log/smarttexttospeech/access.log"
errorlog  = "/var/log/smarttexttospeech/error.log"
loglevel  = "info"

# Process name (visible in ps/top)
proc_name = "smarttexttospeech"
