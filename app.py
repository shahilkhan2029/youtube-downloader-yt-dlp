# app.py
import os
import threading
import queue
import uuid
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from yt_dlp import YoutubeDL

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.dirname(__file__)
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# In-memory task store
tasks = {}          # task_id -> task dict
task_queue = queue.Queue()

# Worker thread processes tasks serially
def worker():
    while True:
        task_id = task_queue.get()
        if task_id is None:
            break
        task = tasks.get(task_id)
        if not task:
            task_queue.task_done()
            continue
        try:
            task['status'] = 'processing'
            if task['mode'] == 'single':
                _download_single(task_id, task)
            elif task['mode'] == 'playlist':
                _download_playlist(task_id, task)
            task['status'] = 'done'
        except Exception as e:
            task['status'] = 'error'
            task['error'] = str(e)
        finally:
            task_queue.task_done()

worker_thread = threading.Thread(target=worker, daemon=True)
worker_thread.start()

# Generic progress hook factory
def make_progress_hook(task_id):
    def progress_hook(d):
        t = tasks.get(task_id)
        if not t:
            return

        status = d.get('status')
        info = d.get('info_dict') or {}
        # playlist_index may appear in info or as a top-level key
        p_idx = info.get('playlist_index') or d.get('playlist_index') or info.get('playlist_index')
        p_total = info.get('playlist_count') or d.get('playlist_count') or None

        if status == 'downloading':
            percent = d.get('percent')
            t['progress'] = {
                'status': 'downloading',
                'percent': round(percent, 2) if percent is not None else None,
                'speed': d.get('speed'),
                'eta': d.get('eta'),
                'filename': d.get('filename'),
                'item': p_idx,
                'of': p_total
            }
        elif status == 'finished':
            fn = d.get('filename')
            # append file name to tasks
            if fn:
                t.setdefault('files', []).append(os.path.basename(fn))
            t['progress'] = {
                'status': 'finished',
                'filename': fn,
                'item': p_idx,
                'of': p_total
            }
        elif status == 'error':
            t['progress'] = {'status': 'error', 'info': d}
    return progress_hook

# Single video download
# Single video download (replace existing function)
def _download_single(task_id, task):
    url = task['url']
    choice = task.get('choice', 'best')
    force_h264 = bool(task.get('force_h264', False))
    audio_format = task.get('audio_format', 'mp3')

    outtmpl = os.path.join(DOWNLOAD_DIR, '%(title)s [%(id)s].%(ext)s')

    ydl_opts = {
        'outtmpl': outtmpl,
        'noplaylist': True,
        'progress_hooks': [make_progress_hook(task_id)],
        'writesubtitles': False,
        'quiet': True,
        'no_warnings': True,
    }

    if choice == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }],
        })
    else:
        # choose format (support numeric heights and 'best')
        if choice == 'best':
            fmt = 'bestvideo+bestaudio/best'
        else:
            try:
                h = int(choice)
                fmt = f'bestvideo[height<={h}]+bestaudio/best'
            except Exception:
                fmt = 'bestvideo+bestaudio/best'
        ydl_opts['format'] = fmt

        # prefer mp4 container when merging (helps Premiere)
        ydl_opts['merge_output_format'] = 'mp4'

        if force_h264:
            # Force re-encode to libx264 + aac by passing ffmpeg args during merge.
            # This is compatible across yt-dlp versions and avoids the problematic postprocessor key.
            ydl_opts['postprocessor_args'] = [
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k'
            ]
            # (No explicit 'postprocessors' with 'preferredformat' here)

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# Playlist download (serial, with numeric prefixes)
# Playlist download (replace existing function)
def _download_playlist(task_id, task):
    url = task['url']
    choice = task.get('choice', 'best')
    force_h264 = bool(task.get('force_h264', False))
    audio_format = task.get('audio_format', 'mp3')

    outtmpl = os.path.join(DOWNLOAD_DIR, '%(playlist_index)03d - %(title)s [%(id)s].%(ext)s')

    ydl_opts = {
        'outtmpl': outtmpl,
        'noplaylist': False,
        'progress_hooks': [make_progress_hook(task_id)],
        'writesubtitles': False,
        'quiet': True,
        'no_warnings': True,
    }

    if choice == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }],
        })
    else:
        if choice == 'best':
            fmt = 'bestvideo+bestaudio/best'
        else:
            try:
                h = int(choice)
                fmt = f'bestvideo[height<={h}]+bestaudio/best'
            except:
                fmt = 'bestvideo+bestaudio/best'
        ydl_opts['format'] = fmt
        ydl_opts['merge_output_format'] = 'mp4'

        if force_h264:
            ydl_opts['postprocessor_args'] = [
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k'
            ]
            # no explicit 'postprocessors' dict with 'preferredformat'

    # Let yt-dlp download the entire playlist in order; the outtmpl includes playlist_index
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


# Routes
@app.route("/")
def index():
    return render_template("index.html")

from werkzeug.utils import secure_filename

ALLOWED_COOKIE_EXTS = {'.txt', '.cookies'}  # Netscape cookies usually .txt

@app.route("/start_download", methods=["POST"])
def start_download():
    """
    Accepts multipart/form-data which may include:
      - url (string)
      - mode (single|playlist)
      - choice (quality)
      - audio_format (mp3|m4a|...)
      - force_h264 (on|off or true/false)
      - cookiefile (file upload - optional, Netscape format)
    """
    # Accept both JSON and form-data gracefully:
    if request.is_json:
        data = request.get_json()
        url = (data.get("url") or "").strip()
        mode = data.get("mode", "single")
        choice = data.get("choice", "best")
        audio_format = data.get("audio_format", "mp3")
        force_h264 = bool(data.get("force_h264", False))
        cookiefile = None
    else:
        # multipart/form-data (from front-end FormData)
        url = (request.form.get("url") or "").strip()
        mode = request.form.get("mode", "single")
        choice = request.form.get("choice", "best")
        audio_format = request.form.get("audio_format", "mp3")
        force_h264 = request.form.get("force_h264") in ("true", "on", "1", "yes", "checked")
        cookiefile = request.files.get("cookiefile")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    task_id = str(uuid.uuid4())

    saved_cookie_path = None
    # If a cookie file was uploaded, validate and save it
    if cookiefile and cookiefile.filename:
        filename = secure_filename(cookiefile.filename)
        _, ext = os.path.splitext(filename)
        if ext.lower() not in ALLOWED_COOKIE_EXTS:
            return jsonify({"error": "Unsupported cookie file extension; upload a .txt (Netscape) cookies file"}), 400
        saved_cookie_name = f"cookies_{task_id}.txt"
        saved_cookie_path = os.path.join(DOWNLOAD_DIR, saved_cookie_name)
        cookiefile.save(saved_cookie_path)
        # make file readable by yt-dlp; optional: set restrictive permissions
        try:
            os.chmod(saved_cookie_path, 0o600)
        except Exception:
            pass

    task = {
        'id': task_id,
        'url': url,
        'mode': mode,
        'choice': choice,
        'audio_format': audio_format,
        'force_h264': force_h264,
        'cookiefile_path': saved_cookie_path,   # may be None
        'status': 'queued',
        'progress': {'status': 'queued'},
        'files': []
    }
    tasks[task_id] = task
    task_queue.put(task_id)
    return jsonify({"task_id": task_id}), 200


@app.route("/task_status/<task_id>")
def task_status(task_id):
    t = tasks.get(task_id)
    if not t:
        return jsonify({"error": "task not found"}), 404
    return jsonify({
        'id': t['id'],
        'status': t.get('status'),
        'progress': t.get('progress'),
        'files': t.get('files'),
        'error': t.get('error')
    })

@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

@app.route("/list_downloads")
def list_downloads():
    files = []
    for f in sorted(os.listdir(DOWNLOAD_DIR)):
        files.append(f)
    return jsonify({'files': files})

if __name__ == "__main__":
    # Note: for production use a proper WSGI server and persistent task queue.
    app.run(debug=True, port=5000)
