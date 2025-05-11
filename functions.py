import os
import re

from PIL import Image
from flask import url_for
from transliterate import translit


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
