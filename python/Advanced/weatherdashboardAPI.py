from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx
import redis
import json
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
import os

app = FastAPI(title="Weather Dashboard API")

# Redis cache setup
cache = redis.Redis(host='localhost', port=6379, decode_responses=True)

# API keys from environment
OPENWEATHER_KEY = os.getenv('OPENWEATHER_KEY', 'demo_key')
WEATHERAPI_KEY = os.getenv('WEATHERAPI_KEY', 'demo_key')

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    condition: str
    humidity: int
    wind_speed: float
    timestamp: str
    source: str

class ForecastResponse(BaseModel):
    location: str
    forecast: List[dict]
    source: str

class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
    
    async def check_rate_limit(self, api_key: str):
        key = f"rate_limit:{api_key}"
        current = cache.get(key)
        
        if current is None:
            cache.setex(key, self.time_window, 1)
            return True
        
        count = int(current)
        if count >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        cache.incr(key)
        return True

rate_limiter = RateLimiter()

async def fetch_openweather(city: str):
    """Fetch weather from OpenWeatherMap API"""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_KEY}&units=metric"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return {
                'location': data['name'],
                'temperature': data['main']['temp'],
                'condition': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'timestamp': datetime.now().isoformat(),
                'source': 'OpenWeatherMap'
            }
    return None

async def fetch_weatherapi(city: str):
    """Fetch weather from WeatherAPI"""
    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            return {
                'location': data['location']['name'],
                'temperature': data['current']['temp_c'],
                'condition': data['current']['condition']['text'],
                'humidity': data['current']['humidity'],
                'wind_speed': data['current']['wind_kph'] / 3.6,
                'timestamp': datetime.now().isoformat(),
                'source': 'WeatherAPI'
            }
    return None

@app.get("/weather/{city}", response_model=WeatherResponse)
async def get_weather(city: str, api_key: str = "default"):
    """Get current weather for a city with caching and API failover"""
    
    # Check rate limit
    await rate_limiter.check_rate_limit(api_key)
    
    # Check cache
    cache_key = f"weather:{city.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return WeatherResponse(**json.loads(cached))
    
    # Try OpenWeatherMap first
    weather_data = await fetch_openweather(city)
    
    # Fallback to WeatherAPI
    if not weather_data:
        weather_data = await fetch_weatherapi(city)
    
    if not weather_data:
        raise HTTPException(status_code=404, detail="City not found")
    
    # Cache for 5 minutes
    cache.setex(cache_key, 300, json.dumps(weather_data))
    
    return WeatherResponse(**weather_data)

@app.get("/forecast/{city}", response_model=ForecastResponse)
async def get_forecast(city: str, days: int = 5, api_key: str = "default"):
    """Get weather forecast for a city"""
    
    await rate_limiter.check_rate_limit(api_key)
    
    cache_key = f"forecast:{city.lower()}:{days}"
    cached = cache.get(cache_key)
    if cached:
        return ForecastResponse(**json.loads(cached))
    
    # Try to get forecast from OpenWeatherMap
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_KEY}&units=metric&cnt={days*8}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            forecast = []
            for item in data['list'][:days]:
                forecast.append({
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'condition': item['weather'][0]['description'],
                    'humidity': item['main']['humidity']
                })
            
            result = {
                'location': data['city']['name'],
                'forecast': forecast,
                'source': 'OpenWeatherMap'
            }
            
            cache.setex(cache_key, 600, json.dumps(result))
            return ForecastResponse(**result)
    
    raise HTTPException(status_code=404, detail="Forecast not available")

@app.get("/weather/history/{city}")
async def get_historical_weather(city: str, date: str, api_key: str = "default"):
    """Get historical weather data for a specific date"""
    
    await rate_limiter.check_rate_limit(api_key)
    
    # Check cache
    cache_key = f"history:{city.lower()}:{date}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # WeatherAPI historical endpoint
    url = f"http://api.weatherapi.com/v1/history.json?key={WEATHERAPI_KEY}&q={city}&dt={date}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            result = {
                'location': data['location']['name'],
                'date': date,
                'temperature': data['forecast']['forecastday'][0]['day']['avgtemp_c'],
                'condition': data['forecast']['forecastday'][0]['day']['condition']['text'],
                'humidity': data['forecast']['forecastday'][0]['day']['avghumidity'],
                'source': 'WeatherAPI'
            }
            
            cache.setex(cache_key, 86400, json.dumps(result))  # Cache for 24 hours
            return result
    
    raise HTTPException(status_code=404, detail="Historical data not available")

@app.get("/weather/bulk")
async def get_bulk_weather(cities: str, api_key: str = "default"):
    """Get weather for multiple cities in parallel"""
    
    await rate_limiter.check_rate_limit(api_key)
    
    city_list = [c.strip() for c in cities.split(',')]
    tasks = [get_weather(city, api_key) for city in city_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    response = []
    for city, result in zip(city_list, results):
        if isinstance(result, Exception):
            response.append({'city': city, 'error': str(result)})
        else:
            response.append({'city': city, 'weather': result.dict()})
    
    return {'results': response}

# Run: uvicorn main:app --reload
# Ensure Redis is running: redis-server
# Install: pip install fastapi uvicorn httpx redis