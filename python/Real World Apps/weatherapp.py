import requests
import os

API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        if response.status_code == 404:
            print(f"City '{city}' not found.")
            return
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return

    data = response.json()
    name = data["name"]
    country = data["sys"]["country"]
    temp = data["main"]["temp"]
    feels = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]
    desc = data["weather"][0]["description"].capitalize()

    print(f"\nWeather in {name}, {country}")
    print(f"  Condition   : {desc}")
    print(f"  Temperature : {temp}°C (Feels like {feels}°C)")
    print(f"  Humidity    : {humidity}%")
    print(f"  Wind Speed  : {wind} m/s\n")


def main():
    print("=== Weather App ===")
    while True:
        city = input("Enter city name (or 'exit'): ").strip()
        if city.lower() == 'exit':
            break
        get_weather(city)


if __name__ == "__main__":
    main()
