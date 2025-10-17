"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'

// Open-Meteo API (free, no API key required!)
const WEATHER_REFRESH_INTERVAL = 30 * 60 * 1000 // 30 minutes

interface WeatherData {
  temp: number
  feels_like: number
  condition: string
  weatherCode: number
  humidity: number
  wind_speed: number
}

interface ForecastDay {
  date: string
  temp_max: number
  temp_min: number
  condition: string
  weatherCode: number
}

interface LocationPreference {
  location_lat?: number
  location_lon?: number
  location_name?: string
  use_browser_location: boolean
}

export default function WeatherWidget() {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [forecast, setForecast] = useState<ForecastDay[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showSettings, setShowSettings] = useState(false)
  const [showLocationPrompt, setShowLocationPrompt] = useState(false)
  const [locationPref, setLocationPref] = useState<LocationPreference | null>(null)
  const [manualLocation, setManualLocation] = useState('')
  const [searchingLocation, setSearchingLocation] = useState(false)

  // Weather code to condition mapping (WMO Weather interpretation codes)
  const getWeatherCondition = (code: number): string => {
    if (code === 0) return 'Clear'
    if (code <= 3) return 'Partly Cloudy'
    if (code <= 48) return 'Foggy'
    if (code <= 57) return 'Drizzle'
    if (code <= 67) return 'Rain'
    if (code <= 77) return 'Snow'
    if (code <= 82) return 'Showers'
    if (code <= 86) return 'Snow Showers'
    if (code <= 99) return 'Thunderstorm'
    return 'Unknown'
  }

  // Weather code to emoji
  const getWeatherEmoji = (code: number, isDay: boolean = true): string => {
    if (code === 0) return isDay ? '☀️' : '🌙'
    if (code <= 3) return isDay ? '🌤️' : '🌙'
    if (code <= 48) return '🌫️'
    if (code <= 57) return '🌦️'
    if (code <= 67) return '🌧️'
    if (code <= 77) return '❄️'
    if (code <= 82) return '🌧️'
    if (code <= 86) return '🌨️'
    if (code <= 99) return '⛈️'
    return '🌡️'
  }

  // Fetch saved location preference from backend
  const fetchLocationPreference = async () => {
    try {
      const response = await api.get('/user/location')
      setLocationPref(response.data)
      return response.data
    } catch (err) {
      console.error('Failed to fetch location preference:', err)
      return null
    }
  }

  // Save location preference to backend
  const saveLocationPreference = async (pref: LocationPreference) => {
    try {
      await api.post('/user/location', pref)
      setLocationPref(pref)
      return true
    } catch (err) {
      console.error('Failed to save location preference:', err)
      showToast('Failed to save location preference', 'error')
      return false
    }
  }

  // Get browser geolocation
  const getBrowserLocation = (): Promise<{ lat: number; lon: number }> => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            lat: position.coords.latitude,
            lon: position.coords.longitude
          })
        },
        (error) => {
          reject(error)
        }
      )
    })
  }

  // Geocode city name using Open-Meteo
  const geocodeCity = async (cityName: string): Promise<{ lat: number; lon: number; name: string } | null> => {
    try {
      const response = await fetch(
        `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(cityName)}&count=1&language=en&format=json`
      )
      const data = await response.json()

      if (data.results && data.results.length > 0) {
        const result = data.results[0]
        return {
          lat: result.latitude,
          lon: result.longitude,
          name: `${result.name}${result.admin1 ? ', ' + result.admin1 : ''}${result.country ? ', ' + result.country : ''}`
        }
      }
      return null
    } catch (err) {
      console.error('Geocoding failed:', err)
      return null
    }
  }

  // Fetch weather data from Open-Meteo
  const fetchWeather = async (lat: number, lon: number) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(
        `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto&forecast_days=6`
      )
      const data = await response.json()

      if (response.ok && data.current) {
        // Set current weather
        setWeather({
          temp: Math.round(data.current.temperature_2m),
          feels_like: Math.round(data.current.apparent_temperature),
          condition: getWeatherCondition(data.current.weather_code),
          weatherCode: data.current.weather_code,
          humidity: data.current.relative_humidity_2m,
          wind_speed: Math.round(data.current.wind_speed_10m)
        })

        // Set 5-day forecast (skip today, show next 5 days)
        if (data.daily) {
          const forecastArray: ForecastDay[] = []
          for (let i = 1; i < Math.min(6, data.daily.time.length); i++) {
            const date = new Date(data.daily.time[i])
            forecastArray.push({
              date: date.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
              }),
              temp_max: Math.round(data.daily.temperature_2m_max[i]),
              temp_min: Math.round(data.daily.temperature_2m_min[i]),
              condition: getWeatherCondition(data.daily.weather_code[i]),
              weatherCode: data.daily.weather_code[i]
            })
          }
          setForecast(forecastArray)
        }
      }
    } catch (err) {
      console.error('Failed to fetch weather:', err)
      setError('Failed to load weather data')
    } finally {
      setLoading(false)
    }
  }

  // Initialize weather data
  const initializeWeather = async () => {
    const pref = await fetchLocationPreference()

    if (pref && pref.location_lat && pref.location_lon) {
      // Use saved location
      await fetchWeather(pref.location_lat, pref.location_lon)
    } else {
      // No saved location - show prompt
      setShowLocationPrompt(true)
      setLoading(false)
    }
  }

  // Handle user allows location
  const handleAllowLocation = async () => {
    setShowLocationPrompt(false)
    setLoading(true)

    try {
      const location = await getBrowserLocation()
      await fetchWeather(location.lat, location.lon)

      // Save preference
      await saveLocationPreference({
        location_lat: location.lat,
        location_lon: location.lon,
        use_browser_location: true
      })
    } catch (err) {
      console.error('Location permission denied:', err)
      setError('Location access denied')
      setLoading(false)
      setShowSettings(true)
    }
  }

  // Handle user declines location
  const handleDeclineLocation = () => {
    setShowLocationPrompt(false)
    setError('Please set your location')
    setShowSettings(true)
  }

  // Handle manual location search
  const handleManualLocationSearch = async () => {
    if (!manualLocation.trim()) return

    setSearchingLocation(true)
    const result = await geocodeCity(manualLocation)
    setSearchingLocation(false)

    if (result) {
      const success = await saveLocationPreference({
        location_lat: result.lat,
        location_lon: result.lon,
        location_name: result.name,
        use_browser_location: false
      })

      if (success) {
        await fetchWeather(result.lat, result.lon)
        setShowSettings(false)
        setManualLocation('')
        showToast(`Location set to ${result.name}`, 'success')
      }
    } else {
      showToast('Location not found. Please try another city.', 'error')
    }
  }

  // Handle use browser location from settings
  const handleUseBrowserLocation = async () => {
    try {
      const location = await getBrowserLocation()
      const success = await saveLocationPreference({
        location_lat: location.lat,
        location_lon: location.lon,
        use_browser_location: true
      })

      if (success) {
        await fetchWeather(location.lat, location.lon)
        setShowSettings(false)
        showToast('Using your current location', 'success')
      }
    } catch (err) {
      showToast('Failed to get browser location', 'error')
    }
  }

  useEffect(() => {
    initializeWeather()

    // Auto-refresh every 30 minutes
    const interval = setInterval(() => {
      if (locationPref?.location_lat && locationPref?.location_lon) {
        fetchWeather(locationPref.location_lat, locationPref.location_lon)
      }
    }, WEATHER_REFRESH_INTERVAL)

    return () => clearInterval(interval)
  }, [])

  // Loading state
  if (loading) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Weather</span>
          <span className="text-sm text-white/50">Loading...</span>
        </h3>
        <div className="space-y-3">
          <div className="skeleton h-24"></div>
          <div className="skeleton h-16"></div>
        </div>
      </div>
    )
  }

  // Error/No data state
  if (error || !weather) {
    return (
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Weather</span>
          <button
            onClick={() => setShowSettings(true)}
            className="text-sm text-purple-400 hover:text-purple-300"
          >
            ⚙️
          </button>
        </h3>
        <div className="flex flex-col items-center justify-center h-32 space-y-3">
          <p className="text-white/50 text-sm text-center">{error || 'No weather data'}</p>
          <button
            onClick={() => setShowSettings(true)}
            className="btn-primary text-sm px-4"
          >
            Set Location
          </button>
        </div>
      </div>
    )
  }

  // Main weather display
  return (
    <>
      <div className="widget-card h-full">
        <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
          <span>Weather</span>
          <button
            onClick={() => setShowSettings(true)}
            className="text-sm text-purple-400 hover:text-purple-300 transition-colors"
            title="Location settings"
          >
            ⚙️
          </button>
        </h3>

        {/* Current Weather */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-5xl font-bold">{weather.temp}°F</div>
              <div className="text-white/50 text-sm mt-1">
                Feels like {weather.feels_like}°F
              </div>
            </div>
            <div className="text-right">
              <div className="text-6xl mb-1">
                {getWeatherEmoji(weather.weatherCode)}
              </div>
              <div className="text-sm font-medium">{weather.condition}</div>
            </div>
          </div>

          {locationPref?.location_name && (
            <div className="text-xs text-white/40 mt-2">
              📍 {locationPref.location_name}
            </div>
          )}
        </div>

        {/* 5-Day Forecast */}
        <div>
          <h4 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">
            5-Day Forecast
          </h4>
          <div className="space-y-2">
            {forecast.map((day, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
              >
                <div className="flex items-center space-x-3 flex-1">
                  <div className="text-2xl">
                    {getWeatherEmoji(day.weatherCode)}
                  </div>
                  <span className="text-sm">{day.date}</span>
                </div>
                <div className="text-sm font-medium">
                  <span className="text-white">{day.temp_max}°</span>
                  <span className="text-white/40 ml-2">{day.temp_min}°</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Location Permission Prompt */}
      {showLocationPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="glass-medium rounded-2xl shadow-2xl w-96 p-6">
            <div className="text-center mb-6">
              <div className="text-5xl mb-4">📍</div>
              <h3 className="text-xl font-semibold mb-2">Enable Location</h3>
              <p className="text-white/70 text-sm">
                We'd like to show you weather for your current location.
                You can always change this later or set it manually.
              </p>
            </div>

            <div className="space-y-3">
              <button
                onClick={handleAllowLocation}
                className="w-full btn-primary flex items-center justify-center space-x-2"
              >
                <span>✓</span>
                <span>Allow Location Access</span>
              </button>

              <button
                onClick={handleDeclineLocation}
                className="w-full px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors text-sm"
              >
                Set Location Manually
              </button>
            </div>

            <p className="text-xs text-white/40 text-center mt-4">
              Your location is only used to fetch weather data and is stored privately.
            </p>
          </div>
        </div>
      )}

      {/* Location Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="glass-medium rounded-2xl shadow-2xl w-96 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold">Location Settings</h3>
              <button
                onClick={() => setShowSettings(false)}
                className="text-white/50 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {/* Current Location */}
              {locationPref?.location_name && (
                <div className="p-3 rounded-lg bg-white/5">
                  <div className="text-xs text-white/50 mb-1">Current Location</div>
                  <div className="text-sm font-medium">📍 {locationPref.location_name}</div>
                </div>
              )}

              {/* Browser Location Button */}
              <button
                onClick={handleUseBrowserLocation}
                className="w-full btn-primary flex items-center justify-center space-x-2"
              >
                <span>🌐</span>
                <span>Use My Current Location</span>
              </button>

              {/* Manual Location Input */}
              <div>
                <label className="text-sm text-white/70 mb-2 block">
                  Or enter a city name:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={manualLocation}
                    onChange={(e) => setManualLocation(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleManualLocationSearch()}
                    placeholder="e.g., San Francisco"
                    className="input flex-1"
                    disabled={searchingLocation}
                  />
                  <button
                    onClick={handleManualLocationSearch}
                    disabled={searchingLocation || !manualLocation.trim()}
                    className="btn-primary px-4"
                  >
                    {searchingLocation ? '...' : 'Set'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
