
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
import logging

from fastapi.responses import FileResponse

from backend.chat_message import ChatMessage
from backend.connection_manager import ConnectionManager
from backend.deps.dependencies import get_connection_manager, get_groq_client, get_mcp_client
from backend.groq_chat_client import GroqChatClient
from backend.mcp_client import MCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def read_root():
    """Serve React app"""
    return FileResponse("frontend/build/index.html")

@router.get("/api/health")
async def health_check(mcp_client: MCPClient = Depends(get_mcp_client), manager: ConnectionManager = Depends(get_connection_manager)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_connected": mcp_client.is_connected,
        "active_connections": len(manager.active_connections)
    }

@router.get("/api/system-info")
async def get_system_info(mcp_client: MCPClient = Depends(get_mcp_client)):
    """Get current system information"""
    try:
        if not mcp_client.is_connected:
            raise HTTPException(status_code=503, detail="MCP server not connected")
        
        system_data = await mcp_client.get_system_info()
        return {
            "success": True,
            "data": system_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat")
async def chat_endpoint(message: ChatMessage, mcp_client: MCPClient = Depends(get_mcp_client), groq_client: GroqChatClient = Depends(get_groq_client)):
    """Process chat message"""
    try:
        if mcp_client.is_connected:
            response = await groq_client.chat(message.message)
        
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))