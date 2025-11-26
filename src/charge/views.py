from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.conf import settings
from django.http import FileResponse, Http404
from django.core.cache import cache
from .forms import MediaDownloadForm
import yt_dlp
import os
import threading
import uuid
from urllib.parse import urlparse
from urllib.request import urlretrieve, Request, urlopen
import zipfile
import re

# Stockage des tâches dans le cache partagé (compatible multi-process)
TASKS_LOCK = threading.Lock()

def _task_key(task_id: str) -> str:
    return f"task:{task_id}"


def index(request: HttpRequest):
    form = MediaDownloadForm()
    return render(request, "charge/index.html", {"form": form})


def _sanitize_filename(name: str, max_len: int = 80) -> str:
    if not name:
        return "media"
    # Remove forbidden characters for Windows and trim
    name = re.sub(r'[<>:"/\\|?*]+', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or "media"


def _allowed_platform(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    allowed_hosts = (
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
        "m.youtube.com",
        "facebook.com",
        "www.facebook.com",
        "fb.watch",
        "instagram.com",
        "www.instagram.com",
        "m.instagram.com",
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        # Twitter / X
        "twitter.com",
        "www.twitter.com",
        "mobile.twitter.com",
        "x.com",
        "www.x.com",
        # Snapchat
        "snapchat.com",
        "www.snapchat.com",
        "story.snapchat.com",
    )
    return any(host in netloc for host in allowed_hosts)


def _format_for(media_type: str, quality: str) -> str:
    if media_type == "video":
        if quality == "best":
            return "bestvideo+bestaudio/best"
        # limite de hauteur si possible
        return f"bv*[height<={quality}]+ba/b[height<={quality}]"
    if media_type == "audio":
        return "bestaudio/best"
    return "best"  # fallback


def _run_download(task_id: str, url: str, media_type: str, quality: str):
    output_root = os.path.join(settings.MEDIA_ROOT, "downloads")
    os.makedirs(output_root, exist_ok=True)

    def progress_hook(d):
        if d.get('status') == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            pct = int(downloaded * 100 / total) if total else 0
            with TASKS_LOCK:
                data = cache.get(_task_key(task_id)) or {}
                data.update({
                    'status': 'downloading',
                    'progress': pct,
                    'speed': d.get('speed'),
                })
                cache.set(_task_key(task_id), data, timeout=60*60)
        elif d.get('status') == 'finished':
            with TASKS_LOCK:
                data = cache.get(_task_key(task_id)) or {}
                data.update({'status': 'processing', 'progress': 95})
                cache.set(_task_key(task_id), data, timeout=60*60)

    try:
        # Cas miniature uniquement (images natives non supportées)
        if media_type in ('image', 'miniature'):
            try:
                with yt_dlp.YoutubeDL({'quiet': True, 'skip_download': True}) as ydl:
                    info = ydl.extract_info(url, download=False)
                thumb_url = info.get('thumbnail')
                if not thumb_url:
                    raise Exception("Miniature indisponible pour cette URL")
                # Build readable filename: 'miniature [id6].ext'
                label = 'miniature'
                vid = (info.get('id') or task_id)[:6]
                ext = os.path.splitext(thumb_url.split('?')[0])[1] or '.jpg'
                if not ext.lower() in ('.jpg', '.jpeg', '.png', '.webp'):
                    ext = '.jpg'
                out_path = os.path.join(output_root, f"{label} [{vid}]{ext}")
                urlretrieve(thumb_url, out_path)
                rel_path = os.path.relpath(out_path, settings.MEDIA_ROOT).replace('\\', '/')
                with TASKS_LOCK:
                    data = cache.get(_task_key(task_id)) or {}
                    data.update({
                        'status': 'finished',
                        'progress': 100,
                        'file_path': out_path,
                        'filename': os.path.basename(out_path),
                        'download_url': settings.MEDIA_URL + rel_path,
                        'message': 'Images non supportées. Miniature téléchargée.'
                    })
                    cache.set(_task_key(task_id), data, timeout=60*60)
                return
            except Exception as e:
                with TASKS_LOCK:
                    data = cache.get(_task_key(task_id)) or {}
                    data.update({'status': 'error', 'error': 'Images non supportées. Miniature uniquement.', 'details': str(e)})
                    cache.set(_task_key(task_id), data, timeout=60*60)
                return

        # Vidéo/Audio via yt-dlp
        ydl_opts = {
            'noplaylist': True,
            # Use id-only filename then rename to 'video|audio [id6].ext' after download
            'outtmpl': os.path.join(output_root, "%(id)s.%(ext)s"),
            'progress_hooks': [progress_hook],
            'format': _format_for(media_type, quality),
            'quiet': True,
            'prefer_ffmpeg': True,
            'windowsfilenames': True,
            'retries': 5,
            'fragment_retries': 5,
            'retry_sleep': {
                'extractor': 2,
                'http': 2,
                'fragment': 2,
                'download': 2,
            },
        }
        # FFmpeg: pointer vers le binaire/dossier fourni OU autodétecter via PATH
        ffmpeg_loc = getattr(settings, 'FFMPEG_LOCATION', None)
        ffmpeg_path = None
        if not ffmpeg_loc:
            try:
                from shutil import which
                ffmpeg_path = which('ffmpeg')
            except Exception:
                ffmpeg_path = None
        else:
            ffmpeg_path = str(ffmpeg_loc)

        if ffmpeg_path:
            # ffmpeg_path peut être un fichier exécutable ou un dossier contenant ffmpeg
            bin_dir = ffmpeg_path
            if os.path.isfile(bin_dir):
                # exécutable direct: prendre le dossier
                bin_dir = os.path.dirname(bin_dir)
                ydl_opts['ffmpeg_location'] = ffmpeg_path
            else:
                # dossier: essayer d'identifier le binaire (linux/mac/windows)
                ffmpeg_exe = os.path.join(bin_dir, 'ffmpeg')
                ffprobe_exe = os.path.join(bin_dir, 'ffprobe')
                if os.name == 'nt':
                    ffmpeg_exe += '.exe'
                    ffprobe_exe += '.exe'
                if os.path.isfile(ffmpeg_exe):
                    ydl_opts['ffmpeg_location'] = ffmpeg_exe
                else:
                    # certains environnements acceptent le dossier directement
                    ydl_opts['ffmpeg_location'] = bin_dir
            # Étendre PATH pour les sous-process
            try:
                os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
            except Exception:
                pass
        if media_type == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        # Déterminer l'hôte cible une seule fois
        host = urlparse(url).netloc.lower()

        # En-têtes HTTP (user-agent) et cookies optionnels
        ua = getattr(settings, 'YTDLP_USER_AGENT', None)
        if ua:
            ydl_opts['http_headers'] = {
                'User-Agent': ua,
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': url,
            }
        # Cookies par plateforme
        cookies_dir = getattr(settings, 'YTDLP_COOKIES_DIR', None)
        cookiefile = getattr(settings, 'YTDLP_COOKIEFILE', None)
        platform_cookie = None
        if cookies_dir:
            cookies_dir = str(cookies_dir)
            if any(h in host for h in ("youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com")):
                candidate = os.path.join(cookies_dir, 'cookies_youtube.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
            elif any(h in host for h in ("facebook.com", "www.facebook.com", "fb.watch")):
                candidate = os.path.join(cookies_dir, 'cookies_facebook.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
            elif any(h in host for h in ("instagram.com", "www.instagram.com", "m.instagram.com")):
                candidate = os.path.join(cookies_dir, 'cookies_instagram.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
            elif any(h in host for h in ("tiktok.com", "www.tiktok.com", "vm.tiktok.com")):
                candidate = os.path.join(cookies_dir, 'cookies_tiktok.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
            elif any(h in host for h in ("twitter.com", "www.twitter.com", "mobile.twitter.com", "x.com", "www.x.com")):
                candidate = os.path.join(cookies_dir, 'cookies_twitter.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
            elif any(h in host for h in ("snapchat.com", "www.snapchat.com", "story.snapchat.com")):
                candidate = os.path.join(cookies_dir, 'cookies_snapchat.txt')
                if os.path.isfile(candidate):
                    platform_cookie = candidate
        if not platform_cookie and cookiefile and os.path.isfile(cookiefile):
            platform_cookie = str(cookiefile)
        if platform_cookie:
            ydl_opts['cookiefile'] = platform_cookie

        # Améliorer la compat YouTube si aucun runtime JS n'est disponible
        if any(h in host for h in ("youtube.com", "youtu.be", "m.youtube.com", "www.youtube.com")):
            ydl_opts.setdefault('extractor_args', {})
            ydl_opts['extractor_args'].setdefault('youtube', {})
            ydl_opts['extractor_args']['youtube']['player_client'] = ['default', 'android', 'web']
            # Réduire certains cas SABR/PO token côté YouTube (sans casser l'existant)
            ydl_opts['extractor_args']['youtube'].setdefault('po_token', ['guide'])

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Pre-extract to get id
            info0 = ydl.extract_info(url, download=False)
            media_id = (info0 or {}).get('id') or ''
            # Download
            ydl.download([url])

        # Trouver le fichier généré
        generated = None
        if media_id:
            needle = f"{media_id}."
            for fname in os.listdir(output_root):
                if fname.startswith(needle):
                    generated = os.path.join(output_root, fname)
                    break
        # Fallback (very unlikely now)
        if not generated:
            # pick the most recently modified file in output_root
            files = [os.path.join(output_root, f) for f in os.listdir(output_root)]
            files = [p for p in files if os.path.isfile(p)]
            generated = max(files, key=os.path.getmtime) if files else None
        if not generated:
            raise Exception("Fichier non trouvé après téléchargement")

        # Rename to readable pattern: 'video|audio [id6].ext'
        base_label = 'video' if media_type == 'video' else ('audio' if media_type == 'audio' else 'media')
        id6 = (media_id or os.path.basename(generated).split('.')[0])[:6]
        ext = os.path.splitext(generated)[1]
        final_path = os.path.join(output_root, f"{base_label} [{id6}]{ext}")
        try:
            if generated != final_path:
                os.replace(generated, final_path)
            out_file = final_path
        except Exception:
            out_file = generated

        rel_path = os.path.relpath(out_file, settings.MEDIA_ROOT).replace('\\', '/')
        with TASKS_LOCK:
            data = cache.get(_task_key(task_id)) or {}
            data.update({
                'status': 'finished',
                'progress': 100,
                'file_path': out_file,
                'filename': os.path.basename(out_file),
                'download_url': settings.MEDIA_URL + rel_path,
                'debug': {
                    'host': host,
                    'cookie_used': platform_cookie,
                    'ffmpeg_used': ydl_opts.get('ffmpeg_location'),
                    'ua_used': ua,
                }
            })
            cache.set(_task_key(task_id), data, timeout=60*60)
    except Exception as e:
        with TASKS_LOCK:
            data = cache.get(_task_key(task_id)) or {}
            # Ajouter un peu de contexte debug sans exposer trop d'infos
            data.update({'status': 'error', 'error': str(e), 'debug': {
                'host': locals().get('host', None),
                'cookie_used': locals().get('platform_cookie', None),
                'ffmpeg_used': locals().get('ydl_opts', {}).get('ffmpeg_location') if 'ydl_opts' in locals() else None,
                'ua_used': locals().get('ua', None),
            }})
            cache.set(_task_key(task_id), data, timeout=60*60)


def start_download(request: HttpRequest):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    form = MediaDownloadForm(request.POST)
    if not form.is_valid():
        return JsonResponse({'error': 'Formulaire invalide', 'details': form.errors}, status=400)

    # Persist the request in DB
    media_obj = form.save()

    url = media_obj.url
    media_type = media_obj.media_type
    quality = media_obj.quality

    if not _allowed_platform(url):
        return JsonResponse({'error': 'Plateforme non supportée ou lien invalide'}, status=400)

    task_id = uuid.uuid4().hex
    with TASKS_LOCK:
        cache.set(_task_key(task_id), {'status': 'queued', 'progress': 0}, timeout=60*60)

    t = threading.Thread(target=_run_download, args=(task_id, url, media_type, quality), daemon=True)
    t.start()
    return JsonResponse({'task_id': task_id})


def progress(request: HttpRequest, task_id: str):
    with TASKS_LOCK:
        data = cache.get(_task_key(task_id))
    if not data:
        return JsonResponse({'error': 'Tâche introuvable'}, status=404)
    return JsonResponse(data)


def download_file(request: HttpRequest, task_id: str):
    with TASKS_LOCK:
        data = cache.get(_task_key(task_id))
    if not data or data.get('status') != 'finished':
        raise Http404('Fichier non prêt')
    file_path = data.get('file_path')
    if not file_path or not os.path.isfile(file_path):
        raise Http404('Fichier introuvable')
    filename = data.get('filename') or os.path.basename(file_path)
    return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
