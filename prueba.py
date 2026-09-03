import requests

headers = {
    "Origin": "https://rakuten.tv",
    "Referer": "https://rakuten.tv/",
    "User_Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:98.0) Gecko/20100101 Firefox/98.0"
}

query = {
    "classification_id": 5,
    "device_identifier": "web",
    "device_stream_audio_quality": "2.0",
    "device_stream_hdr_type": "NONE",
    "device_stream_video_quality": "FHD",
    "disable_dash_legacy_packages": False,
    "locale": "es",
    "market_code": "es"
}

payload = {
    "audio_language": "ENG",
    "audio_quality": "2.0",
    "classification_id": 5,
    "content_id": "france-24-en",
    "content_type": "live_channels",
    "device_serial": "not implemented",
    "player": "web:HLS-NONE:NONE",
    "strict_video_quality": False,
    "subtitle_language": "MIS",
    "video_type": "stream"
}

r = requests.post(
    "https://gizmo.rakuten.tv/v3/avod/streamings",
    headers=headers,
    params=query,
    json=payload
)

print("STATUS:", r.status_code)
print(r.text)