from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai import Credentials
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import TextContent
import os
import asyncio

load_dotenv()

# ---------- IBM Credentials ----------
credentials = Credentials(
    url=os.getenv("IBM_URL"),
    api_key=os.getenv("IBM_API_KEY")
)

model = ModelInference(
    model_id="ibm/granite-4-h-small",
    credentials=credentials,
    project_id=os.getenv("PROJECT_ID"),
    params={
        "temperature": 0.3,
        "max_new_tokens": 200
    }
)

# ---------- MCP CALL ----------
async def call_weather_tool(city: str):
    server_params = StdioServerParameters(
        command="python",
        args=["weather-mcp-server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_weather",
                {"city": city}
            )
            for item in result.content:
                if isinstance(item, TextContent):
                    return item.text
    return "No response from weather tool."


# ---------- AGENT ----------
async def run_agent(user_input: str):

    if "weather" in user_input.lower():
        city = user_input.split()[-1].replace("?", "")
        return await call_weather_tool(city)

    response = model.generate_text(
        prompt=f"User: {user_input}\nAssistant:"
    )
    return response


# ---------- RUN ----------
if __name__ == "__main__":
    user_query = input("Ask something: ")
    result = asyncio.run(run_agent(user_query))
    print("\nAgent Response:")
    print(result)
