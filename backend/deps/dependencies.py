from fastapi import Request

from backend.connection_manager import ConnectionManager
from backend.groq_chat_client import GroqChatClient
from backend.mcp_client import MCPClient


def get_mcp_client(request: Request) -> MCPClient:
    return request.app.state.mcp_client


def get_groq_client(request: Request) -> GroqChatClient:
    return request.app.state.groq_client


def get_connection_manager(request: Request) -> ConnectionManager:
    return request.app.state.connection_manager
