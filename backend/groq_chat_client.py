
import json
import logging
from groq import Groq

from backend.mcp_client import MCPClient 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqChatClient:
    """Groq client for AI chat functionality"""
    
    def __init__(self, api_key: str, mcp_client: MCPClient):
        self.api_key = api_key
        self.conversation_history = []
        self.mcp_client = mcp_client
        self.groq_client = Groq(api_key=api_key)
        
        self.conversation_history = [{
            "role": "system",
            "content": """You are a helpful system administrator assistant. You have access to real-time system information.

            When users ask about system performance, hardware, or computer status, provide helpful interpretations including:
            - Whether resource usage levels are normal or concerning
            - Suggestions for optimization if needed  
            - Clear explanations of technical terms
            - Actionable recommendations when appropriate

            Be conversational, helpful, and technically accurate. Keep responses concise but informative."""
                    }]
    
    async def chat(self, message: str) -> str:
        """Process chat message with system context"""
        try:                
            self.conversation_history.append({
                "role": "user",
                "content": message
            })
            
            response = await self._get_groq_response()
            
            self.conversation_history.append({
                "role": "assistant", 
                "content": response
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return "I'm sorry, I encountered an error processing your request. Please try again."
    
    async def _get_groq_response(self) -> str:
        """Generate contextual response based on system data"""
        tools = self.mcp_client.get_tools_for_groq()    
        response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.conversation_history,
                tools=tools if tools else None,
                tool_choice="auto" if tools else "none",
                temperature=0.1,
                max_tokens=1024
            )
            
        message = response.choices[0].message
        
        if message.tool_calls:
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function", 
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except:
                    function_args = {}
                
                print(f"Calling tool: {function_name}")
                
                tool_result = await self.mcp_client.call_tool(
                    function_name, function_args
                )
                
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })
            
            final_response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.conversation_history,
                temperature=0.1,
                max_tokens=1024
            )
            
            assistant_response = final_response.choices[0].message.content
            
        else:
            assistant_response = message.content
        
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        return assistant_response
