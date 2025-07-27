import asyncio
import json
import sys
import psutil
import platform
from datetime import datetime

def get_system_info():
    """Get all system information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        memory = psutil.virtual_memory()
        
        partitions = psutil.disk_partitions()
        disks = []
        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percentage": round((usage.used / usage.total) * 100, 2)
                })
            except (PermissionError, FileNotFoundError):
                continue
        
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "system": {
                "platform": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "uptime_hours": round(uptime.total_seconds() / 3600, 1),
            "cpu": {
                "cores": psutil.cpu_count(),
                "usage_percent": round(sum(cpu_percent) / len(cpu_percent), 1),
                "frequency_mhz": cpu_freq.current if cpu_freq else "N/A"
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "usage_percent": memory.percent
            },
            "disks": disks,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def handle_jsonrpc():
    """Handle JSON-RPC communication"""
    print("System Info MCP Server started", file=sys.stderr)
    
    tools = [
        {
            "name": "get_system_info",
            "description": "Get comprehensive system information including CPU, memory, disk usage, and system details",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    ]
    
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            message = json.loads(line.strip())
            response = None
            
            if message.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "system-info-server",
                            "version": "1.0.0"
                        }
                    }
                }
                
            elif message.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0", 
                    "id": message.get("id"),
                    "result": {
                        "tools": tools
                    }
                }
                
            elif message.get("method") == "tools/call":
                params = message.get("params", {})
                tool_name = params.get("name")
                
                if tool_name == "get_system_info":
                    system_info = get_system_info()
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(system_info, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    }
            
            if response:
                print(json.dumps(response), flush=True)
                
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            continue

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("=== SYSTEM INFO TEST ===")
        info = get_system_info()
        print(json.dumps(info, indent=2))
    else:
        asyncio.run(handle_jsonrpc())