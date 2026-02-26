from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("multi-tools-server")

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


@mcp.tool()
def get_random_joke() -> str:
    """
    Get a random programming joke.
    """
    try:
        url = "https://official-joke-api.appspot.com/jokes/programming/random"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data and len(data) > 0:
            joke = data[0]
            return f"😄 {joke['setup']}\n\n{joke['punchline']}"
        return "😅 Couldn't fetch a joke right now!"
    except Exception as e:
        return f"❌ Error getting joke: {str(e)}"


@mcp.tool()
def get_random_fact() -> str:
    """
    Get a random interesting fact.
    """
    try:
        url = "https://uselessfacts.jsph.pl/random.json?language=en"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        fact = data.get("text", "No fact available")
        return f"💡 Did you know?\n\n{fact}"
    except Exception as e:
        return f"❌ Error getting fact: {str(e)}"


@mcp.tool()
def get_crypto_price(crypto: str = "bitcoin") -> str:
    """
    Get current cryptocurrency price in USD.
    Supported: bitcoin, ethereum, dogecoin, cardano, solana, etc.
    """
    try:
        crypto = crypto.lower().strip()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if crypto in data:
            price = data[crypto]["usd"]
            change = data[crypto].get("usd_24h_change", 0)
            change_emoji = "📈" if change > 0 else "📉"
            
            return f"💰 {crypto.capitalize()}: ${price:,.2f} USD\n{change_emoji} 24h Change: {change:.2f}%"
        return f"❌ Cryptocurrency '{crypto}' not found. Try: bitcoin, ethereum, dogecoin"
    except Exception as e:
        return f"❌ Error getting crypto price: {str(e)}"


if __name__ == "__main__":
    mcp.run()

# Made with Bob
