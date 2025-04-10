import requests
import re
from deep_translator import GoogleTranslator

WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(location, api_key):
    try:
        if re.search(r"[^\x00-\x7F]", location):
            location_query = GoogleTranslator(source="ja", target="en").translate(
                location
            )
        else:
            location_query = location

        params = {
            "q": location_query,
            "appid": api_key,
            "units": "metric",
            "lang": "ja",
        }
        response = requests.get(WEATHER_API_URL, params=params)
        data = response.json()
        weather_info = (
            f"{data['name']}の天気: {data['weather'][0]['description']}\n"
            f"気温: {data['main']['temp']}℃ / 湿度: {data['main']['humidity']}%"
        )
        return weather_info

    except Exception as e:
        return f"天気情報の取得に失敗: {str(e)}"
