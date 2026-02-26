import streamlit as st
import asyncio
import json
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai import Credentials
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp.client.stdio import StdioServerParameters
from mcp.types import TextContent
import os

load_dotenv()

# ---------- IBM Granite Setup ----------
try:
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
            "max_new_tokens": 500
        }
    )
except Exception as e:
    st.error(f"Failed to initialize IBM Watsonx: {str(e)}")
    st.stop()

# ---------- Available Tools ----------
AVAILABLE_TOOLS = {
    "get_weather": {
        "description": "Get current weather information for a specific city",
        "parameters": ["city"],
        "example": "What's the weather in London?"
    },
    "get_random_joke": {
        "description": "Get a random programming joke",
        "parameters": [],
        "example": "Tell me a joke"
    },
    "get_random_fact": {
        "description": "Get a random interesting fact",
        "parameters": [],
        "example": "Tell me an interesting fact"
    },
    "get_crypto_price": {
        "description": "Get current cryptocurrency price in USD (bitcoin, ethereum, dogecoin, etc.)",
        "parameters": ["crypto"],
        "example": "What's the price of bitcoin?"
    }
}

# ---------- MCP Tool Call ----------
async def call_mcp_tool(tool_name: str, parameters: dict = {}):
    """Generic function to call any MCP tool"""
    try:
        server = StdioServerParameters(
            command="python",
            args=["tools-mcp-server.py"]
        )
        
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call the tool with parameters if provided
                if parameters:
                    result = await session.call_tool(tool_name, parameters)
                else:
                    result = await session.call_tool(tool_name, {})
                
                for item in result.content:
                    if isinstance(item, TextContent):
                        return item.text
        
        return f"No response from {tool_name} tool."
    except Exception as e:
        return f"Error calling {tool_name}: {str(e)}"

# ---------- LLM-Based Tool Selection ----------
def analyze_intent_with_llm(user_input: str) -> dict:
    """Use LLM to determine if a tool should be called and extract parameters"""
    
    tools_description = "\n".join([
        f"- {name}: {info['description']}"
        for name, info in AVAILABLE_TOOLS.items()
    ])
    
    prompt = f"""You are an AI assistant that analyzes user queries and determines if any tools should be called.

Available tools:
{tools_description}

User query: "{user_input}"

Analyze the query and respond ONLY with valid JSON in this exact format:
{{
    "needs_tool": true,
    "tool_name": "get_weather",
    "parameters": {{"city": "CityName"}},
    "reasoning": "User asked about weather"
}}

OR if no tool is needed:
{{
    "needs_tool": false,
    "tool_name": null,
    "parameters": null,
    "reasoning": "General conversation"
}}

Rules:
- If query mentions weather/temperature/climate, use get_weather tool and extract city name
- If query asks for joke/humor, use get_random_joke tool (no parameters needed)
- If query asks for fact/trivia, use get_random_fact tool (no parameters needed)
- If query asks for crypto/bitcoin/ethereum price, use get_crypto_price tool and extract crypto name
- For general conversation, set needs_tool to false
- Respond with ONLY the JSON object, no other text

JSON Response:"""
    
    try:
        response = model.generate_text(prompt=prompt)
        
        # Clean and extract JSON more robustly
        response = response.strip()
        
        # Remove markdown code blocks
        if "```json" in response.lower():
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.split("```")[1].split("```")[0].strip()
        
        # Find JSON object boundaries
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start == -1 or end <= start:
            raise ValueError("No valid JSON found in response")
        
        json_str = response[start:end]
        result = json.loads(json_str)
        
        # Validate required fields
        if "needs_tool" not in result:
            raise ValueError("Missing 'needs_tool' field")
        
        return result
        
    except Exception as e:
        # Silent fallback to keyword matching - no warning shown to user
        user_lower = user_input.lower()
        
        # Weather detection
        if "weather" in user_lower or "temperature" in user_lower:
            words = user_input.lower().split()
            city = ""
            for i, word in enumerate(words):
                if word in ["in", "at", "for"] and i + 1 < len(words):
                    city = words[i + 1].replace("?", "").replace(".", "").replace(",", "")
                    break
            if not city:
                city = words[-1].replace("?", "").replace(".", "").replace(",", "")
            return {
                "needs_tool": True,
                "tool_name": "get_weather",
                "parameters": {"city": city.capitalize()},
                "reasoning": "Weather query detected"
            }
        
        # Joke detection
        if "joke" in user_lower or "funny" in user_lower:
            return {
                "needs_tool": True,
                "tool_name": "get_random_joke",
                "parameters": {},
                "reasoning": "Joke request detected"
            }
        
        # Fact detection
        if "fact" in user_lower or "trivia" in user_lower:
            return {
                "needs_tool": True,
                "tool_name": "get_random_fact",
                "parameters": {},
                "reasoning": "Fact request detected"
            }
        
        # Crypto detection
        if "crypto" in user_lower or "bitcoin" in user_lower or "ethereum" in user_lower:
            crypto = "bitcoin"
            if "ethereum" in user_lower:
                crypto = "ethereum"
            elif "dogecoin" in user_lower:
                crypto = "dogecoin"
            return {
                "needs_tool": True,
                "tool_name": "get_crypto_price",
                "parameters": {"crypto": crypto},
                "reasoning": "Crypto price query detected"
            }
        
        return {
            "needs_tool": False,
            "tool_name": None,
            "parameters": None,
            "reasoning": "General conversation"
        }

# ---------- Agent Logic ----------
async def run_agent(user_input: str):
    """Main agent logic with LLM-based tool selection"""
    
    # Use LLM to analyze intent
    intent = analyze_intent_with_llm(user_input)
    
    # If tool is needed, call it
    if intent.get("needs_tool"):
        tool_name = intent.get("tool_name")
        parameters = intent.get("parameters", {})
        
        if tool_name in AVAILABLE_TOOLS:
            # Call the appropriate tool
            tool_output = await call_mcp_tool(tool_name, parameters)
            return tool_output, True, intent.get("reasoning", ""), tool_name
        else:
            return f"Tool '{tool_name}' not found.", False, "", None
    
    # Otherwise, use LLM for general conversation
    try:
        response = model.generate_text(
            prompt=f"You are a helpful AI assistant. Respond naturally to the user.\n\nUser: {user_input}\nAssistant:"
        )
        return response, False, intent.get("reasoning", ""), None
    except Exception as e:
        return f"Error generating response: {str(e)}", False, "", None

# ---------- Streamlit UI ----------
st.set_page_config(
    page_title="🤖 AI Agent with MCP Tools",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI - Dark theme with softer colors
st.markdown("""
<style>
    /* Main background - Dark gradient */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* User message specific styling */
    .stChatMessage[data-testid="user-message"] {
        background-color: rgba(94, 129, 244, 0.15);
        border-left: 3px solid #5e81f4;
    }
    
    /* Assistant message specific styling */
    .stChatMessage[data-testid="assistant-message"] {
        background-color: rgba(46, 213, 115, 0.1);
        border-left: 3px solid #2ed573;
    }
    
    /* Sidebar - Darker gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f3460 0%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Sidebar content */
    [data-testid="stSidebar"] .element-container {
        color: #e0e0e0;
    }
    
    /* Headers */
    h1 {
        color: #5e81f4 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-weight: 700;
    }
    
    h2, h3 {
        color: #a8b2d1 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Success boxes */
    .stSuccess {
        background-color: rgba(46, 213, 115, 0.15);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border-left: 4px solid #2ed573;
        color: #2ed573 !important;
    }
    
    /* Info boxes */
    .stInfo {
        background-color: rgba(94, 129, 244, 0.15);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border-left: 4px solid #5e81f4;
        color: #a8b2d1 !important;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: rgba(255, 159, 67, 0.15);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border-left: 4px solid #ff9f43;
    }
    
    /* Error boxes */
    .stError {
        background-color: rgba(238, 82, 83, 0.15);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border-left: 4px solid #ee5253;
    }
    
    /* Input box */
    .stChatInputContainer {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px;
    }
    
    /* Text input styling */
    .stTextInput input {
        background-color: rgba(255, 255, 255, 0.05);
        color: #e0e0e0;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    /* Button styling - Brighter */
    .stButton button {
        background: linear-gradient(135deg, #6c8ff7 0%, #5a7de6 100%);
        color: white !important;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        font-size: 1rem;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #5a7de6 0%, #4a6dd6 100%);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
    }
    
    /* Expander styling - Better visibility */
    .streamlit-expanderHeader {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        color: #d0dcff !important;
        font-weight: 500;
    }
    
    .streamlit-expanderContent {
        background-color: rgba(255, 255, 255, 0.03);
        color: #e8e8e8 !important;
    }
    
    /* Caption text - Brighter */
    .stCaption {
        color: #b0b8d0 !important;
        font-size: 0.95rem;
    }
    
    /* All paragraph text - Ensure visibility */
    p {
        color: #e8e8e8 !important;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #e8e8e8 !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #5e81f4 !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .stApp {
            padding: 10px;
        }
        
        h1 {
            font-size: 1.8rem !important;
        }
        
        h2 {
            font-size: 1.4rem !important;
        }
        
        .stChatMessage {
            padding: 10px;
            margin: 5px 0;
        }
        
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
    }
    
    @media (max-width: 480px) {
        h1 {
            font-size: 1.5rem !important;
        }
        
        .stButton button {
            padding: 8px 15px;
            font-size: 0.9rem;
        }
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(94, 129, 244, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(94, 129, 244, 0.7);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛠️ Agent Configuration")
    st.markdown("---")
    
    st.subheader("📋 Available Tools")
    for tool_name, tool_info in AVAILABLE_TOOLS.items():
        with st.expander(f"🔧 {tool_name}"):
            st.write(f"**Description:** {tool_info['description']}")
            st.write(f"**Parameters:** {', '.join(tool_info['parameters'])}")
            st.write(f"**Example:** {tool_info['example']}")
    
    st.markdown("---")
    st.subheader("ℹ️ About")
    st.info("""
    This AI agent uses:
    - **IBM Granite LLM** for intelligent responses
    - **LLM-based tool selection** to automatically detect when to use tools
    - **MCP (Model Context Protocol)** for tool integration
    """)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main content
st.title("🤖 AI Agent with MCP Tools")
st.caption("Powered by IBM Granite + Intelligent Tool Selection")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("tool_used"):
            st.success(f"🔧 Tool Used: {message.get('tool_name', 'Unknown')}")
        if message.get("reasoning"):
            with st.expander("🧠 Agent Reasoning"):
                st.write(message["reasoning"])

# Chat input
if prompt := st.chat_input("Ask me anything... (e.g., 'What's the weather in Paris?')"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                response, used_tool, reasoning, tool_name = asyncio.run(run_agent(prompt))
                
                st.write(response)
                
                if used_tool:
                    st.success(f"🔧 Tool Used: {tool_name}")
                
                if reasoning:
                    with st.expander("🧠 Agent Reasoning"):
                        st.write(reasoning)
                
                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "tool_used": used_tool,
                    "tool_name": tool_name,
                    "reasoning": reasoning
                })
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "tool_used": False
                })

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: white; opacity: 0.7;'>"
    "Built with ❤️ using Streamlit, IBM Watsonx, and MCP"
    "</div>",
    unsafe_allow_html=True
)

# Made with Bob
