import json

import httpx

from bot import config

CONDITIONS = {
    "clear": "ясно",
    "partly-cloudy": "малооблачно",
    "cloudy": "облачно с прояснениями",
    "overcast": "пасмурно",
    "drizzle": "морось",
    "light-rain": "небольшой дождь",
    "rain": "дождь",
    "moderate-rain": "умеренно сильный",
    "heavy-rain": "сильный дождь",
    "continuous-heavy-rain": "длительный сильный дождь",
    "showers": "ливень",
    "wet-snow": "дождь со снегом",
    "light-snow": "небольшой снег",
    "snow": "снег",
    "snow-showers": "снегопад",
    "hail": "град",
    "thunderstorm": "гроза",
    "thunderstorm-with-rain": "дождь с грозой",
    "thunderstorm-with-hail": "гроза с градом",
}

WIND_DIR = {
    "nw": "северо-западное",
    "n": "северное",
    "ne": "северо-восточное",
    "e": "восточное",
    "se": "юго-восточное",
    "s": "южное",
    "sw": "юго-западное",
    "w": "западное",
    "с": "штиль",
}


async def yandex_weather(latitude, longitude, api_key=config.get_settings().YANDEX_API_KEY):
    url_yandex = f"https://api.weather.yandex.ru/v2/informers?lat={latitude}&lon={longitude}&[lang=ru_RU]"

    headers = {
        "X-Yandex-API-Key": api_key,
        "Content-type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url_yandex, headers=headers)
        response.raise_for_status()
        yandex_json = json.loads(response.text)

    yandex_json["fact"]["condition"] = CONDITIONS[yandex_json["fact"]["condition"]]
    yandex_json["fact"]["wind_dir"] = WIND_DIR[yandex_json["fact"]["wind_dir"]]
    for parts in yandex_json["forecast"]["parts"]:
        parts["condition"] = CONDITIONS[parts["condition"]]
        parts["wind_dir"] = WIND_DIR[parts["wind_dir"]]

    weather = {}
    params = ["condition", "wind_dir", "pressure_mm", "humidity"]
    for parts in yandex_json["forecast"]["parts"]:
        weather[parts["part_name"]] = {"temp": parts["temp_avg"]}
        for param in params:
            weather[parts["part_name"]][param] = parts[param]

    weather["fact"] = {"temp": yandex_json["fact"]["temp"]}
    for param in params:
        weather["fact"][param] = yandex_json["fact"][param]

    weather["link"] = yandex_json["info"]["url"]

    return weather


def format_weather_text(dict_weather_yandex):
    day = {
        "night": "ночью",
        "morning": "утром",
        "day": "днем",
        "evening": "вечером",
        "fact": "сейчас",
    }

    message = ""

    for i in dict_weather_yandex.keys():
        if i != "link":
            time_day = day[i]
            temp = (
                "+" + str(dict_weather_yandex[i]["temp"])
                if dict_weather_yandex[i]["temp"] > 0
                else str(dict_weather_yandex[i]["temp"])
            )
            message += (f"Температура {time_day} {temp}, " f'{dict_weather_yandex[i]["condition"]}\n',)[0]

    return message


async def get_moscow_weather_text():
    weather = await yandex_weather(55.75396, 37.620393)  # Moscow
    return format_weather_text(weather)
