import yt_dlp

ffbin = r"C:\Users\DELL\Desktop\challenge\download\src\download\ffmpeg\bin"

opts = {
    'quiet': False,
    'prefer_ffmpeg': True,
    'ffmpeg_location': ffbin,
    'postprocessors': [
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }
    ],
}

print("Using ffmpeg_location:", opts['ffmpeg_location'])

with yt_dlp.YoutubeDL(opts) as ydl:
    ydl.download(["https://youtu.be/6Hgj9m7s9gg?si=b3zeTKXHPgTZDXU5"])

print("TEST FINI ✔️")