from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("weather-server")

@mcp.tool()
def get_weather(city: str) -> str:
    """
    Get current weather for a city.
    """
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=20)
        data = response.json()

        current = data["current_condition"][0]
        temp = current["temp_C"]
        desc = current["weatherDesc"][0]["value"]

        return f"🌤️ Weather in {city}: {temp}°C, {desc}"
    except Exception as e:
        return f"❌ Error getting weather: {str(e)}"

if __name__ == "__main__":
    mcp.run()

# Made with Bob
