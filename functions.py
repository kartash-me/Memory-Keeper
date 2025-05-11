import base64
import datetime as dt
import os
import re
from io import BytesIO

import exifread
import requests
from PIL import Image
from dotenv import load_dotenv
from flask import url_for
from transliterate import translit


def get_api_key(key_name):
    key = os.environ.get(key_name)

    if key is None:
        if os.path.exists(".env"):
            load_dotenv(".env")
        elif os.path.exists("template.env"):
            load_dotenv("template.env")
        else:
            raise KeyError("Файл .env не найден")

        key = os.environ.get(key_name)

        if key is None:
            raise KeyError("API-ключ не найден")

    return key


GEOCODE_API_KEY = get_api_key("GEOCODE_API_KEY")


def make_preview(file_storage) -> str:
    img = Image.open(file_storage)
    img.thumbnail((400, 400), Image.Resampling.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{data}"


def extract_photo_metadata(image_path):
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f, details=False)

    def get_decimal_coords(tags_local):
        try:
            lat_ref = tags_local["GPS GPSLatitudeRef"].printable
            lat_raw = tags_local["GPS GPSLatitude"].values
            lon_ref = tags_local["GPS GPSLongitudeRef"].printable
            lon_raw = tags_local["GPS GPSLongitude"].values

            def safe_div(val):
                return float(val.num) / float(val.den) if val.den != 0 else 0.0

            lat = [safe_div(x) for x in lat_raw]
            lon = [safe_div(x) for x in lon_raw]

            lat_decimal = lat[0] + lat[1] / 60 + lat[2] / 3600
            if lat_ref != 'N':
                lat_decimal = -lat_decimal

            lon_decimal = lon[0] + lon[1] / 60 + lon[2] / 3600
            if lon_ref != 'E':
                lon_decimal = -lon_decimal

            return round(lat_decimal, 6), round(lon_decimal, 6)
        except (KeyError, ZeroDivisionError, IndexError):
            return None, None

    def get_datetime_obj(tags_local):
        dt_str = None
        for tag_name in (
            "EXIF DateTimeOriginal",
            "EXIF DateTimeDigitized",
                "Image DateTime"):
            if tag_name in tags_local:
                dt_str = tags_local[tag_name].printable
                break

        if dt_str:
            try:
                return dt.datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S')
            except ValueError:
                return None
        return None

    latitude, longitude = get_decimal_coords(tags)
    timestamp_obj = get_datetime_obj(tags)

    if latitude is None and timestamp_obj is None:
        return {
            "latitude": None,
            "longitude": None,
            "timestamp": None
        }

    return {
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": timestamp_obj
    }


def get_address_from_coords(latitude, longitude):
    if latitude is None or longitude is None:
        return None

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": GEOCODE_API_KEY,
        "geocode": f"{longitude},{latitude}",
        "format": "json",
        "lang": "ru_RU"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        features = data["response"]["GeoObjectCollection"]["featureMember"]
        if features:
            return features[0]["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]["text"]
        else:
            return None
    except Exception as e:
        print(f"Ошибка геокодирования: {e}")
        return None


def get_coords_from_address(address_string):
    if not address_string:
        return None, None

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": GEOCODE_API_KEY,
        "geocode": address_string,
        "format": "json",
        "lang": "ru_RU",
        "results": 1
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        features = data["response"]["GeoObjectCollection"]["featureMember"]
        if features:
            coords_str = features[0]["GeoObject"]["Point"]["pos"]
            lon_str, lat_str = coords_str.split()
            return float(lat_str), float(lon_str)
        else:
            return None, None
    except Exception as e:
        print(
            f"Ошибка обратного геокодирования для адреса '{address_string}': {e}")
        return None, None


def get_avatar(user):
    if user.avatar:
        return "data:image/png;base64," + user.avatar
    return url_for("static", filename="img/avatar.png")


def get_days_message(days):
    if days % 10 == 1 and days % 100 != 11:
        form = "день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        form = "дня"
    else:
        form = "дней"

    ranges = [
        (0, "Только что с нами!", "&#127881;"),
        (1, "Уже целых", "&#10024;"),
        (4, "Ого, мы", "&#128293;"),
        (11, "Вау, уже", "&#127775;"),
        (31, "Вот это да,", "&#127775;"),
        (91, "Давний пользователь!", "&#9877;")
    ]
    limit, message, emoji = ranges[-1]

    for limit, message, emoji in ranges[::-1]:
        if days > limit:
            break

    return f"{message} {days} {form} вместе {emoji}"


def human_read_format(size):
    values = ["Б", "КБ", "МБ", "ГБ"]
    cnt = 0

    while size > 1023:
        size /= 1024
        cnt += 1

        if cnt == 3:
            break

    return f"{round(size)}{values[cnt]}"


def normalize_filename(filename):
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^\w\-]", "", name)
    name = name.replace(" ", "_")
    name = translit(name, "ru", reversed=True)

    return f"{name}{ext}"


def ru_date(date):
    eng = date.strftime("%d %b %Y").split()
    months = {
        "Jan": "января", "Feb": "февраля", "Mar": "марта", "Apr": "апреля",
        "May": "мая", "Jun": "июня", "Jul": "июля", "Aug": "августа",
        "Sep": "сентября", "Oct": "октября", "Nov": "ноября", "Dec": "декабря"
    }
    eng[1] = months[eng[1]]
    return " ".join(eng) + " г."


def thumbnail(path):
    img = Image.open(path)
    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
    img.info = {}
    tmb_path = "{}_tmb{}".format(*os.path.splitext(path))
    img.save(tmb_path, quality=100, optimize=True)
    return tmb_path
