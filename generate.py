from lxml import etree
import requests
from datetime import datetime, timedelta, time as dt_time, timezone
import pytz
import unicodedata
import time
import json as json_module

tz = pytz.timezone('Europe/Madrid')


def remove_control_characters(s):
    if s is None:
        return None
    return "".join(
        ch for ch in s
        if unicodedata.category(ch)[0] != "C"
    )


def get_days() -> list:
    now = datetime.now().replace(
        hour=datetime.now().hour,
        minute=0,
        second=0,
        microsecond=0
    )

    day_1 = (
        datetime.combine(datetime.now(), dt_time(0, 0))
        + timedelta(days=1)
    )

    day_2 = (
        datetime.combine(datetime.now(), dt_time(0, 0))
        + timedelta(days=2)
    )

    day_3 = (
        datetime.combine(datetime.now(), dt_time(0, 0))
        + timedelta(days=3)
    )

    return [now, day_1, day_2, day_3]


def build_xmltv(channels: list, programmes: list) -> bytes:

    dt_format = "%Y%m%d%H%M%S %z"

    def _to_tz_str(val):

        if isinstance(val, datetime):

            v = val

            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            return v.astimezone(tz).strftime(dt_format)

        return datetime.fromtimestamp(
            val,
            timezone.utc
        ).astimezone(tz).strftime(dt_format)

    data = etree.Element("tv")

    data.set(
        "generator-info-name",
        "rakuten-es-epg"
    )

    data.set(
        "generator-info-url",
        "https://github.com/bitos2002/rakuten-es-epg"
    )

    for ch in channels:

        channel = etree.SubElement(
            data,
            "channel"
        )

        channel.set(
            "id",
            str(ch.get("id"))
        )

        name = etree.SubElement(
            channel,
            "display-name"
        )

        name.set(
            "lang",
            "es"
        )

        name.text = ch.get("name")

        if ch.get("icon"):

            icon_src = etree.SubElement(
                channel,
                "icon"
            )

            icon_src.set(
                "src",
                ch.get("icon")
            )

    for pr in programmes:

        programme = etree.SubElement(
            data,
            "programme"
        )

        programme.set(
            "channel",
            str(pr.get("channel_id"))
        )

        programme.set(
            "start",
            _to_tz_str(pr.get("starts_at"))
        )

        programme.set(
            "stop",
            _to_tz_str(pr.get("ends_at"))
        )

        title = etree.SubElement(
            programme,
            "title"
        )

        title.set(
            "lang",
            "es"
        )

        title.text = pr.get("title")

        if pr.get("subtitle"):

            subtitle = etree.SubElement(
                programme,
                "sub-title"
            )

            subtitle.set(
                "lang",
                "es"
            )

            subtitle.text = remove_control_characters(
                pr.get("subtitle")
            )

        if pr.get("description"):

            description = etree.SubElement(
                programme,
                "desc"
            )

            description.set(
                "lang",
                "es"
            )

            description.text = remove_control_characters(
                pr.get("description")
            )

        if pr.get("tags"):

            for tag in pr.get("tags"):

                category = etree.SubElement(
                    programme,
                    "category"
                )

                category.set(
                    "lang",
                    "es"
                )

                category.text = tag.get("name")

    return etree.tostring(
        data,
        pretty_print=True,
        encoding="utf-8"
    )


days = get_days()

url_string = (
    f"classification_id=5"
    f"&device_identifier=web"
    f"&device_stream_audio_quality=2.0"
    f"&device_stream_hdr_type=NONE"
    f"&device_stream_video_quality=FHD"
    f"&epg_duration_minutes=360"
    f"&epg_ends_at={days[-1].strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
    f"&epg_ends_at_timestamp={days[-1].timestamp()}"
    f"&epg_starts_at={days[0].strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
    f"&epg_starts_at_timestamp={days[0].timestamp()}"
    f"&locale=es"
    f"&market_code=es"
    f"&per_page=250"
)

url = (
    "https://gizmo.rakuten.tv/v3/live_channels?"
    + url_string.replace(":", "%3A")
)

print("Grabbing data")

headers = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.rakuten.tv/",
}

res = None

for attempt in range(5):

    print(f"Attempt {attempt + 1}/5")

    try:

        res = requests.get(
            url,
            headers=headers,
            timeout=60
        )

        print(f"HTTP Status: {res.status_code}")

        if res.status_code == 200:
            break

    except Exception as e:

        print(f"Request error: {e}")

    if attempt < 4:
        print("Waiting 30 seconds before retry...")
        time.sleep(30)

if res is None or res.status_code != 200:

    raise ConnectionError(
        f"HTTP{res.status_code if res else 'NO_RESPONSE'}: could not get info from server!"
    )

json = res.json()["data"]

print("\n========================================")
print("FIRST CHANNEL IDS")
print("========================================")

for channel in json[:50]:

    print(
        f"id={channel.get('id')} | "
        f"numerical_id={channel.get('numerical_id')} | "
        f"title={channel.get('title')}"
    )


print(f"Retrieved {len(json)} channels")

print("\n========================================")
print("FIRST CHANNEL COMPLETE")
print("========================================")

first_channel = json[0]

print(
    f"ID: {first_channel.get('id')}"
)

print(
    f"NUMERICAL_ID: {first_channel.get('numerical_id')}"
)

with open(
    "first_channel_complete.json",
    "w",
    encoding="utf-8"
) as f:

    json_module.dump(
        first_channel,
        f,
        indent=2,
        ensure_ascii=False
    )

print("first_channel_complete.json generated")

print("\n========================================")
print("FIRST CHANNEL DEBUG")
print("========================================")

print(
    json_module.dumps(
        json[0],
        indent=2,
        ensure_ascii=False
    )
)

print("\n========================================")
print("CHANNEL KEYS")
print("========================================")

for key in json[0].keys():
    print(key)

with open(
    "debug_channel.json",
    "w",
    encoding="utf-8"
) as f:

    json_module.dump(
        json[0],
        f,
        indent=2,
        ensure_ascii=False
    )

print("debug_channel.json generated")

with open(
    "channel_keys.txt",
    "w",
    encoding="utf-8"
) as f:

    for key in json[0].keys():
        f.write(f"{key}\n")

print("channel_keys.txt generated")

with open(
    "all_channels.json",
    "w",
    encoding="utf-8"
) as f:

    json_module.dump(
        json,
        f,
        indent=2,
        ensure_ascii=False
    )

print("all_channels.json generated")

with open(
    "all_channel_ids.json",
    "w",
    encoding="utf-8"
) as f:

    json_module.dump(
        [
            {
                "id": ch.get("id"),
                "numerical_id": ch.get("numerical_id"),
                "title": ch.get("title")
            }
            for ch in json
        ],
        f,
        indent=2,
        ensure_ascii=False
    )

print("all_channel_ids.json generated")

for channel in json[:20]:

    print(
        f"ID={channel.get('id')} "
        f"NUMERICAL_ID={channel.get('numerical_id')} "
        f"TITLE={channel.get('title')}"
    )


SEARCH_TERMS = [
    "url",
    "stream",
    "play",
    "video",
    "manifest",
    "source",
    "media",
    "live"
]

found_keys = set()


def scan_object(obj, prefix=""):

    if isinstance(obj, dict):

        for key, value in obj.items():

            full_key = (
                f"{prefix}.{key}"
                if prefix
                else key
            )

            if any(
                term in key.lower()
                for term in SEARCH_TERMS
            ):
                found_keys.add(full_key)

            scan_object(
                value,
                full_key
            )

    elif isinstance(obj, list):

        for item in obj:
            scan_object(item, prefix)


scan_object(json)

print("\n========================================")
print("POSSIBLE STREAM KEYS")
print("========================================")

for key in sorted(found_keys):
    print(key)

with open(
    "possible_stream_keys.txt",
    "w",
    encoding="utf-8"
) as f:

    for key in sorted(found_keys):
        f.write(key + "\n")

print("possible_stream_keys.txt generated")

channels_data = []
programme_data = []

for channel in json:

    ch_id = channel["id"]

    ch_icon = None

    if channel.get("images"):

        images = channel["images"]

        if images.get("artwork_negative"):
            ch_icon = images["artwork_negative"]

        elif images.get("artwork"):
            ch_icon = images["artwork"]

    ch_tags = None

    if channel.get("labels"):

        labels = channel["labels"]

        if labels.get("tags"):
            ch_tags = labels["tags"]

    channels_data.append({
        "name": channel["title"],
        "epg_number": channel.get("channel_number"),
        "id": ch_id,
        "icon": ch_icon,
        "language": "es",
        "tags": ch_tags
    })

    for item in channel["live_programs"]:

        start = datetime.strptime(
            item["starts_at"],
            "%Y-%m-%dT%H:%M:%S.000%z"
        )

        end = datetime.strptime(
            item["ends_at"],
            "%Y-%m-%dT%H:%M:%S.000%z"
        )

        programme_data.append({
            "title": item["title"],
            "subtitle": item["subtitle"],
            "description": item["description"],
            "starts_at": start,
            "ends_at": end,
            "channel_id": ch_id,
            "language": "es",
            "tags": ch_tags,
        })

gap_threshold = 60

programme_data.sort(
    key=lambda p: (
        p["channel_id"],
        p["starts_at"]
    )
)

by_channel = {}

for p in programme_data:
    by_channel.setdefault(
        p["channel_id"],
        []
    ).append(p)

for ch_id, plist in by_channel.items():

    for i in range(len(plist) - 1):

        cur = plist[i]
        nxt = plist[i + 1]

        if nxt["starts_at"] <= cur["ends_at"]:

            cur["ends_at"] = nxt["starts_at"]

        else:

            gap = (
                nxt["starts_at"]
                - cur["ends_at"]
            ).total_seconds()

            if gap <= gap_threshold:

                cur["ends_at"] = nxt["starts_at"]

channel_xml = build_xmltv(
    channels_data,
    programme_data
)

with open("epg.xml", "wb") as f:
    f.write(channel_xml)

print("epg.xml generated successfully")
print("\n========================================")
print("DEBUG FILES GENERATED")
print("========================================")
print("debug_channel.json")
print("channel_keys.txt")
print("all_channels.json")
print("possible_stream_keys.txt")