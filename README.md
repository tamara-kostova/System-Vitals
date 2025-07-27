# System Info Dashboard with MCP and Groq AI Integration

A real-time system monitoring dashboard backed by a FastAPI backend, a JSON-RPC MCP (Modular Command Protocol) server for system info, and an AI-powered chat assistant using Groq LLM.

---

## Overview

This project provides a web-based system info dashboard that monitors CPU, memory, disk usage, uptime, and other system metrics, and allows interactive chatting with an AI assistant that can access live system information.

Key features include:

- **FastAPI backend:** Serves API endpoints and WebSocket connections.
- **MCP server:** A Python JSON-RPC subprocess (`src/server.py`) that gathers rich system info using `psutil` and serves it over a line-oriented JSON-RPC protocol.
- **MCP Client:** Manages launching and communicating with the MCP server asynchronously, exposing tools such as `get_system_info`.
- **Groq LLM integration:** Provides a conversational interface powered by Groq's large language model, capable of invoking MCP tools to enrich system-related responses.
- **React frontend:** Real-time UI with WebSocket interaction, displaying system stats and chat interface featuring Tailwind CSS styling.

---

## Architecture

- The MCP server runs as a subprocess, communicating over stdin/stdout using JSON-RPC.
- The MCP client launches this subprocess and acts as a bridge for system info retrieval.
- Groq LLM chat integrates the MCP tools using function call semantics, allowing the assistant to fetch live system info dynamically.
- The frontend connects via WebSockets to receive live system metrics and chat responses.

---

## Getting Started

`pip install -r requirements.txt`

`uvicorn backend.main:app`

`npm install`

`npm start`
