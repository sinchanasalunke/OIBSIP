import requests
import pyttsx3

API_KEY = "8986cbaa6f7a4756bc0badf2b2ef6623"

city = input("Enter city name: ")

url = "https://api.openweathermap.org/data/2.5/weather"

params = {
    "q": city,
    "appid": API_KEY,
    "units": "metric"
}

try:
    response = requests.get(url, params=params, timeout=10)

    if response.status_code == 200:
        data = response.json()

        city_name = data["name"]
        temperature = data["main"]["temp"]
        weather = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        print("\n----- WEATHER REPORT -----")
        print("City:", city_name)
        print("Temperature:", temperature, "°C")
        print("Weather:", weather)
        print("Humidity:", humidity, "%")
        print("Wind Speed:", wind_speed, "m/s")

        # Create the spoken weather report
        report = (
            f"Here is the weather report for {city_name}. "
            f"The temperature is {temperature} degrees Celsius. "
            f"The weather condition is {weather}. "
            f"The humidity is {humidity} percent. "
            f"The wind speed is {wind_speed} meters per second."
        )

        # Speak the report automatically
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.say(report)
        engine.runAndWait()
        engine.stop()

    elif response.status_code == 401:
        print("Invalid API key. Please check your API key.")

    elif response.status_code == 404:
        print("City not found. Please enter a valid city name.")

    else:
        print("Unable to retrieve weather information.")

except requests.exceptions.Timeout:
    print("Request timed out. Please try again.")

except requests.exceptions.RequestException:
    print("Network error. Check your internet connection.")

except (RuntimeError, OSError) as error:
    print("Weather was retrieved, but voice output failed:", error)