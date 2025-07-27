import asyncio

from contextlib import asynccontextmanager
import json
from datetime import datetime
import logging

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.connection_manager import ConnectionManager
from backend.groq_chat_client import GroqChatClient
from backend.mcp_client import MCPClient
from backend.routes.api import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.mcp_client = MCPClient()
    app.state.groq_client = GroqChatClient(mcp_client=app.state.mcp_client, api_key="")
    app.state.connection_manager = ConnectionManager()
    logger.info("Starting System Monitor API...")

    success = await app.state.mcp_client.start()
    if not success:
        logger.error("Failed to start MCP client")
    else:
        logger.info("System Monitor API started successfully")

    app.state.broadcast_task = asyncio.create_task(broadcast_system_data())
    try:
        yield
    finally:
        await app.state.mcp_client.close()
        logger.info("Shutting down System Monitor API...")

app = FastAPI(title="System Monitor API", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

async def broadcast_system_data():
    """Periodically broadcast system data to all connected clients"""
    while True:
        try:
            if app.state.mcp_client.is_connected and app.state.connection_manager.active_connections:
                system_data = await app.state.mcp_client.get_system_info()
                await app.state.connection_manager.broadcast({
                    "type": "system_data",
                    "data": system_data,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                logger.error(f"MCP Client connection: {app.state.mcp_client.is_connected}")
                logger.error(f"Connection manager connections: {app.state.connection_manager.active_connections}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(10)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await app.state.connection_manager.connect(websocket)
    try:
        if app.state.mcp_client.is_connected:
            try:
                system_data = await app.state.mcp_client.get_system_info()
                await websocket.send_text(json.dumps({
                    "type": "system_data",
                    "data": system_data,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error sending initial data: {e}")
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "chat":
                    response = await app.state.groq_client.chat(message.get("message", ""))
                    await websocket.send_text(json.dumps({
                        "type": "chat_response",
                        "response": response,
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        app.state.connection_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )