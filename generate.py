from lxml import etree
import requests
from datetime import datetime, timedelta, time as dt_time, timezone
import pytz
import unicodedata
import time

tz = pytz.timezone("Europe/Madrid")


def remove_control_characters(s):
    if s is None:
        return None

    return "".join(
        ch for ch in s
        if unicodedata.category(ch)[0] != "C"
    )


def get_days():
    now = datetime.now().replace(
        minute=0,
        second=0,
        microsecond=0
    )

    day_1 = (
        datetime.combine(
            datetime.now(),
            dt_time(0, 0)
        ) + timedelta(days=1)
    )

    day_2 = (
        datetime.combine(
            datetime.now(),
            dt_time(0, 0)
        ) + timedelta(days=2)
    )

    day_3 = (
        datetime.combine(
            datetime.now(),
            dt_time(0, 0)
        ) + timedelta(days=3)
    )

    return [now, day_1, day_2, day_3]


def build_xmltv(channels, programmes):

    dt_format = "%Y%m%d%H%M%S %z"

    def _to_tz_str(val):

        if isinstance(val, datetime):

            if val.tzinfo is None:
                val = val.replace(
                    tzinfo=timezone.utc
                )

            return val.astimezone(tz).strftime(
                dt_format
            )

        return datetime.fromtimestamp(
            val,
            timezone.utc
        ).astimezone(tz).strftime(
            dt_format
        )

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
            str(ch["id"])
        )

        name = etree.SubElement(
            channel,
            "display-name"
        )

        name.set(
            "lang",
            "es"
        )

        name.text = ch["name"]

        if ch.get("icon"):

            icon = etree.SubElement(
                channel,
                "icon"
            )

            icon.set(
                "src",
                ch["icon"]
            )

    for pr in programmes:

        programme = etree.SubElement(
            data,
            "programme"
        )

        programme.set(
            "channel",
            str(pr["channel_id"])
        )

        programme.set(
            "start",
            _to_tz_str(
                pr["starts_at"]
            )
        )

        programme.set(
            "stop",
            _to_tz_str(
                pr["ends_at"]
            )
        )

        title = etree.SubElement(
            programme,
            "title"
        )

        title.set(
            "lang",
            "es"
        )

        title.text = pr["title"]

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
                pr["subtitle"]
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

            description.text = (
                remove_control_characters(
                    pr["description"]
                )
            )

        if pr.get("tags"):

            for tag in pr["tags"]:

                category = etree.SubElement(
                    programme,
                    "category"
                )

                category.set(
                    "lang",
                    "es"
                )

                category.text = tag.get(
                    "name"
                )

    return etree.tostring(
        data,
        pretty_print=True,
        encoding="utf-8"
    )


def get_stream_url(channel, session, headers):

    languages = (
        channel.get("labels", {})
               .get("languages", [])
    )

    if not languages:
        print(f"No language: {channel['id']}")
        return None

    payload = {
        "audio_language": languages[0]["id"],
        "audio_quality": "2.0",
        "classification_id": 5,
        "content_id": channel["id"],
        "content_type": "live_channels",
        "device_serial": "not implemented",
        "player": "web:HLS-NONE:NONE",
        "strict_video_quality": False,
        "subtitle_language": "MIS",
        "video_type": "stream"
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

    try:

        response = session.post(
            "https://gizmo.rakuten.tv/v3/avod/streamings",
            headers=headers,
            params=query,
            json=payload,
            timeout=60
        )

        print(
            channel["id"],
            response.status_code
        )

        data = response.json()

        stream_infos = (
            data.get("data", {})
                .get("stream_infos", [])
        )

        if not stream_infos:
            print(data)
            return None

        url = stream_infos[0].get("url")

        if not url:
            print(data)
            return None

        return (
            url.partition(".m3u8")[0]
            + ".m3u8"
        )

    except Exception as e:

        print(
            f"{channel['id']} -> {e}"
        )

        return None


def generate_m3u(
        channels,
        headers
):

    print(
        "Generating rakuten.m3u..."
    )

    session = requests.Session()

    with open(
        "rakuten.m3u",
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for channel in channels:

            stream_url = (
                get_stream_url(
                    channel,
                    session,
                    headers
                )
            )

            if not stream_url:
                continue

            logo = ""

            images = channel.get(
                "images",
                {}
            )

            if images:

                logo = (
                    images.get(
                        "artwork_negative"
                    )
                    or images.get(
                        "artwork"
                    )
                    or ""
                )

            title = channel["title"]

            f.write(
                f'#EXTINF:-1 '
                f'tvg-id="{channel["id"]}" '
                f'tvg-name="{title}" '
                f'tvg-logo="{logo}",'
                f'{title}\n'
            )

            f.write(
                stream_url + "\n"
            )

    print(
        "rakuten.m3u generated successfully"
    )


print("Grabbing data")

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
    + url_string.replace(
        ":",
        "%3A"
    )
)

headers = {
    "Origin": "https://rakuten.tv",
    "Referer": "https://rakuten.tv/",
    "User_Agent": "Mozilla/5.0 ..."
}

res = None

for attempt in range(5):

    try:

        print(
            f"Attempt {attempt + 1}/5"
        )

        res = requests.get(
            url,
            headers=headers,
            timeout=60
        )

        if res.status_code == 200:
            break

    except Exception as e:

        print(
            f"Request error: {e}"
        )

    if attempt < 4:
        time.sleep(30)

if res is None or res.status_code != 200:

    raise ConnectionError(
        "Unable to retrieve live channels"
    )

channels_json = (
    res.json()["data"]
)

channels_data = []
programme_data = []

for channel in channels_json:

    ch_id = channel["id"]

    ch_icon = None

    images = channel.get(
        "images",
        {}
    )

    if images:

        ch_icon = (
            images.get(
                "artwork_negative"
            )
            or images.get(
                "artwork"
            )
        )

    labels = channel.get(
        "labels",
        {}
    )

    ch_tags = labels.get(
        "tags"
    )

    channels_data.append(
        {
            "name": channel["title"],
            "epg_number": channel.get(
                "channel_number"
            ),
            "id": ch_id,
            "icon": ch_icon,
            "language": "es",
            "tags": ch_tags,
        }
    )

    for item in channel.get(
        "live_programs",
        []
    ):

        start = datetime.strptime(
            item["starts_at"],
            "%Y-%m-%dT%H:%M:%S.000%z"
        )

        end = datetime.strptime(
            item["ends_at"],
            "%Y-%m-%dT%H:%M:%S.000%z"
        )

        programme_data.append(
            {
                "title": item["title"],
                "subtitle": item["subtitle"],
                "description": item["description"],
                "starts_at": start,
                "ends_at": end,
                "channel_id": ch_id,
                "language": "es",
                "tags": ch_tags,
            }
        )

programme_data.sort(
    key=lambda p: (
        p["channel_id"],
        p["starts_at"]
    )
)

by_channel = {}

for prog in programme_data:

    by_channel.setdefault(
        prog["channel_id"],
        []
    ).append(prog)

gap_threshold = 60

for plist in by_channel.values():

    for i in range(
        len(plist) - 1
    ):

        current = plist[i]
        nxt = plist[i + 1]

        if (
            nxt["starts_at"]
            <= current["ends_at"]
        ):

            current["ends_at"] = (
                nxt["starts_at"]
            )

        else:

            gap = (
                nxt["starts_at"]
                - current["ends_at"]
            ).total_seconds()

            if gap <= gap_threshold:

                current["ends_at"] = (
                    nxt["starts_at"]
                )

channel_xml = build_xmltv(
    channels_data,
    programme_data
)

with open(
    "epg.xml",
    "wb"
) as f:

    f.write(channel_xml)

print(
    "epg.xml generated successfully"
)

generate_m3u(
    channels_json,
    headers
)

