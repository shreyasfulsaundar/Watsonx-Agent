# 🤖 AI Agent with MCP Tools

A sophisticated AI chatbot built from scratch using IBM Watsonx AI (Granite models) and Model Context Protocol (MCP) for tool integration. Features intelligent LLM-based tool selection, multiple free API integrations, and a modern, responsive Streamlit UI.

## ✨ Features

- **🧠 LLM-Based Tool Selection**: Uses IBM Granite to intelligently determine when to call tools based on user intent
- **🛠️ 4 Integrated MCP Tools**: Using free APIs
  - 🌤️ Weather information (wttr.in)
  - 😄 Programming jokes (official-joke-api)
  - 💡 Random facts (uselessfacts)
  - 💰 Cryptocurrency prices (CoinGecko)
- **💬 Natural Conversations**: Handles both tool-based queries and general conversations
- **🎨 Modern UI**: Dark-themed, responsive Streamlit interface with excellent contrast
- **📊 Transparent Reasoning**: Shows agent's decision-making process
- **🔄 Real-time Updates**: Async tool execution with live feedback
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Streamlit Web App)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│                         (app.py)                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              IBM Granite LLM (Intent Analyzer)           │  │
│  │  • Analyzes user query                                   │  │
│  │  • Determines if tool is needed                          │  │
│  │  • Extracts parameters                                   │  │
│  │  • Routes to appropriate handler                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│              ┌──────────────┴──────────────┐                   │
│              ▼                              ▼                   │
│  ┌─────────────────────┐      ┌─────────────────────┐         │
│  │   Tool Required?    │      │  General Question?  │         │
│  │        YES          │      │        NO           │         │
│  └──────────┬──────────┘      └──────────┬──────────┘         │
│             │                             │                     │
│             ▼                             ▼                     │
│  ┌─────────────────────┐      ┌─────────────────────┐         │
│  │  Call MCP Tool      │      │  Generate Response  │         │
│  │  via call_mcp_tool()│      │  via IBM Granite    │         │
│  └──────────┬──────────┘      └──────────┬──────────┘         │
└─────────────┼─────────────────────────────┼───────────────────┘
              │                             │
              ▼                             │
┌─────────────────────────────────────────┐ │
│        MCP Server Layer                 │ │
│     (tools-mcp-server.py)               │ │
│  ┌────────────────────────────────────┐ │ │
│  │  Tool 1: get_weather               │ │ │
│  │  Tool 2: get_random_joke           │ │ │
│  │  Tool 3: get_random_fact           │ │ │
│  │  Tool 4: get_crypto_price          │ │ │
│  └────────────────────────────────────┘ │ │
└──────────────────┬──────────────────────┘ │
                   │                         │
                   ▼                         │
┌─────────────────────────────────────────┐ │
│         External APIs                   │ │
│  • wttr.in (Weather)                    │ │
│  • official-joke-api (Jokes)            │ │
│  • uselessfacts.jsph.pl (Facts)         │ │
│  • api.coingecko.com (Crypto)           │ │
└─────────────────────────────────────────┘ │
                   │                         │
                   └─────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Final Response │
                    │   to User       │
                    └─────────────────┘
```



## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- IBM Watsonx AI account
- IBM Cloud API key and project ID

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd watsonx-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   IBM_API_KEY=your_ibm_api_key_here
   IBM_URL=https://us-south.ml.cloud.ibm.com
   PROJECT_ID=your_project_id_here
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Access the app**
   
   Open your browser and navigate to `http://localhost:8501`

## 📁 Project Structure

```
watsonx-agent/
├── app.py                    # Main Streamlit application with UI and logic
├── tools-mcp-server.py       # Unified MCP server with all 4 tools
├── weather-mcp-server.py     # Legacy weather-only server (deprecated)
├── main.py                   # CLI version (optional)
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
└── README.md                # This file
```

### Key Files Explained

- **`app.py`**: Main application containing:
  - Streamlit UI configuration and styling
  - IBM Granite LLM initialization
  - Intent analysis logic (`analyze_intent_with_llm`)
  - Agent routing logic (`run_agent`)
  - MCP tool calling function (`call_mcp_tool`)
  - Chat interface and session management

- **`tools-mcp-server.py`**: MCP server containing:
  - 4 tool definitions using `@mcp.tool()` decorator
  - External API integrations
  - Error handling and response formatting

## 🔧 How It Works

### 1. **LLM-Based Tool Selection**

Instead of manual keyword matching, the agent uses IBM Granite to analyze user intent:

```python
# Traditional approach (manual) ❌
if "weather" in user_input.lower():
    call_weather_tool()

# Our approach (LLM-based) ✅
intent = analyze_intent_with_llm(user_input)
if intent["needs_tool"]:
    call_appropriate_tool(intent["tool_name"], intent["parameters"])
```

**Benefits:**
- Understands natural language variations
- Extracts parameters intelligently
- Handles ambiguous queries
- Extensible to new tools without code changes

### 2. **MCP Tool Integration**

Tools are defined using the Model Context Protocol:

```python
@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    url = f"https://wttr.in/{city}?format=j1"
    response = requests.get(url, timeout=20)
    data = response.json()
    return formatted_result
```

### 3. **Async Execution**

All tool calls are asynchronous for better performance:

```python
async def call_mcp_tool(tool_name: str, parameters: dict = {}):
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, parameters)
            return result
```

## 🛠️ Available Tools

| Tool | Description | Parameters | Example Query | API Used |
|------|-------------|------------|---------------|----------|
| 🌤️ `get_weather` | Get current weather for any city | `city` (string) | "What's the weather in Tokyo?" | wttr.in |
| 😄 `get_random_joke` | Get a random programming joke | None | "Tell me a joke" | official-joke-api |
| 💡 `get_random_fact` | Get a random interesting fact | None | "Tell me a fact" | uselessfacts |
| 💰 `get_crypto_price` | Get cryptocurrency price in USD | `crypto` (string) | "What's the price of ethereum?" | CoinGecko |

## 💡 Usage Examples

### 🌤️ Weather Queries
```
User: What's the weather in London?
Agent: 🔧 Tool Used: get_weather
       🌤️ Weather in London: 15°C, Partly cloudy
```

### 😄 Get a Joke
```
User: Tell me a programming joke
Agent: 🔧 Tool Used: get_random_joke
       😄 Why do programmers prefer dark mode?
       
       Because light attracts bugs!
```

### 💡 Random Facts
```
User: Tell me an interesting fact
Agent: 🔧 Tool Used: get_random_fact
       💡 Did you know?
       
       Honey never spoils. Archaeologists have found 3000-year-old 
       honey in Egyptian tombs that was still edible.
```

### 💰 Cryptocurrency Prices
```
User: What's the price of bitcoin?
Agent: 🔧 Tool Used: get_crypto_price
       💰 Bitcoin: $45,234.56 USD
       📈 24h Change: 3.45%
```

### 💬 General Conversation
```
User: Explain what machine learning is
Agent: Machine learning is a subset of artificial intelligence that 
       enables systems to learn and improve from experience without 
       being explicitly programmed...
```

## 🎨 UI Features

- **Dark Theme**: Softer dark gradient (#1e1e2e to #2a2a3e) with excellent contrast
- **Responsive Design**: Adapts to all screen sizes (desktop, tablet, mobile)
- **Brighter Text**: High-contrast text (#e8e8e8) for better readability
- **Chat History**: Persistent conversation history within session
- **Tool Indicators**: Visual feedback showing which tool was used
- **Reasoning Display**: Expandable section showing agent's decision process
- **Smooth Animations**: Hover effects and transitions for better UX
- **Custom Scrollbars**: Styled scrollbars matching the theme

## 🔧 Adding New Tools

### Step 1: Add Tool to MCP Server

Edit `tools-mcp-server.py`:

```python
@mcp.tool()
def your_new_tool(param: str) -> str:
    """
    Description of what your tool does.
    """
    try:
        # Call your free API
        url = f"https://api.example.com/{param}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Format and return result
        return f"✨ Result: {data['result']}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

### Step 2: Register in App

Edit `app.py` - Add to `AVAILABLE_TOOLS`:

```python
AVAILABLE_TOOLS = {
    # ... existing tools ...
    "your_new_tool": {
        "description": "What your tool does",
        "parameters": ["param"],
        "example": "Example usage"
    }
}
```

### Step 3: Update LLM Prompt

Edit `app.py` - Update rules in `analyze_intent_with_llm()`:

```python
Rules:
- If query asks for X, use your_new_tool and extract param
- ...
```

### Step 4: Add Fallback (Optional)

Edit `app.py` - Add keyword detection in exception handler:

```python
if "keyword" in user_lower:
    return {
        "needs_tool": True,
        "tool_name": "your_new_tool",
        "parameters": {"param": extracted_value},
        "reasoning": "Keyword detected"
    }
```

## 🔒 Security Notes

- Never commit your `.env` file (already in `.gitignore`)
- Keep your IBM API key secure
- Use environment variables for all sensitive data
- Validate all user inputs before processing
- Rate limit API calls to external services
- Handle API errors gracefully

## 🐛 Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### MCP Server Not Starting
```bash
# Test the MCP server directly
python tools-mcp-server.py
```

### Model Deprecation Warning
The app uses `ibm/granite-4-h-small` (recommended model). If you see warnings:
```python
# Update in app.py
model_id="ibm/granite-4-h-small"
```

### LLM Not Detecting Tools
- Check if the query matches the rules in `analyze_intent_with_llm()`
- Verify tool is registered in `AVAILABLE_TOOLS`
- Check fallback logic is working (keyword detection)

### API Timeout Errors
- Increase timeout in tool functions (default: 10-20 seconds)
- Check your internet connection
- Verify the external API is accessible

## 📊 Performance

- **Response Time**: 
  - General queries: < 2 seconds
  - Tool execution: 3-5 seconds (depends on external API)
- **Memory Usage**: ~200MB average
- **Concurrent Users**: Supports multiple Streamlit sessions
- **API Rate Limits**: Respects free tier limits of external APIs

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **IBM Watsonx AI** for the Granite language models
- **Model Context Protocol (MCP)** for tool integration framework
- **Streamlit** for the web framework
- **Free APIs**:
  - wttr.in for weather data
  - official-joke-api for programming jokes
  - uselessfacts.jsph.pl for random facts
  - CoinGecko for cryptocurrency prices

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using IBM Watsonx, MCP, and Streamlit**