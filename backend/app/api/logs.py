"""
API routes for log streaming and retrieval.
I don't really think this is usefull so will remove it once i make sure that there is no need for this one.
"""
import asyncio
import json
from datetime import datetime
from typing import Optional

import docker
from fastapi import (APIRouter, HTTPException, Query, WebSocket,
                     WebSocketDisconnect)
from pydantic import BaseModel

router = APIRouter()


class LogResponse(BaseModel):
    """Log response model."""
    logs: str
    container_id: str
    timestamp: str


@router.websocket("/api/logs/stream")
async def stream_logs(websocket: WebSocket, container_id: str):
    """Stream logs from a container via WebSocket."""
    await websocket.accept()
    
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Check if container is running
        if container.status != 'running':
            await websocket.send_text(json.dumps({
                "error": "Container is not running",
                "container_id": container_id
            }))
            return
        
        # Stream logs
        logs = container.logs(stream=True, timestamps=True, tail=0)
        
        for log_line in logs:
            try:
                # Decode log line
                log_text = log_line.decode('utf-8').strip()
                if log_text:
                    # Send log line to client
                    await websocket.send_text(json.dumps({
                        "log": log_text,
                        "container_id": container_id,
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for container {container_id}")
                break
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "error": f"Error processing log: {str(e)}",
                    "container_id": container_id
                }))
                
    except docker.errors.NotFound:
        await websocket.send_text(json.dumps({
            "error": "Container not found",
            "container_id": container_id
        }))
    except Exception as e:
        await websocket.send_text(json.dumps({
            "error": f"Failed to stream logs: {str(e)}",
            "container_id": container_id
        }))
    finally:
        await websocket.close()


@router.get("/api/logs/raw", response_model=LogResponse)
async def get_raw_logs(
    container_id: str,
    from_ts: Optional[str] = Query(None, description="Start timestamp (ISO format)"),
    to_ts: Optional[str] = Query(None, description="End timestamp (ISO format)"),
    tail: int = Query(100, description="Number of lines to return")
) -> LogResponse:
    """Get raw logs from a container."""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Get logs
        logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
        
        # Filter by timestamp if provided
        if from_ts or to_ts:
            filtered_logs = []
            for line in logs.split('\n'):
                if not line.strip():
                    continue
                    
                # Parse timestamp from log line (format: 2024-01-01T12:00:00.000000000Z log message)
                try:
                    timestamp_str = line[:30]  # Extract timestamp part
                    log_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Apply filters
                    if from_ts:
                        from_dt = datetime.fromisoformat(from_ts.replace('Z', '+00:00'))
                        if log_timestamp < from_dt:
                            continue
                    
                    if to_ts:
                        to_dt = datetime.fromisoformat(to_ts.replace('Z', '+00:00'))
                        if log_timestamp > to_dt:
                            continue
                    
                    filtered_logs.append(line)
                except:
                    # If timestamp parsing fails, include the line
                    filtered_logs.append(line)
            
            logs = '\n'.join(filtered_logs)
        
        return LogResponse(
            logs=logs,
            container_id=container_id,
            timestamp=datetime.now().isoformat()
        )
        
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/api/logs/stats")
async def get_log_stats(container_id: str):
    """Get log statistics for a container."""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Get basic container info
        container_info = {
            "id": container.id,
            "name": container.name,
            "status": container.status,
            "created": container.attrs.get('Created', 'unknown'),
            "image": container.image.tags[0] if container.image.tags else "unknown"
        }
        
        # Get log file size if available
        try:
            logs = container.logs(tail=1).decode('utf-8')
            log_lines = len(logs.split('\n')) if logs else 0
            container_info["log_lines"] = log_lines
        except:
            container_info["log_lines"] = 0
        
        return container_info
        
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log stats: {str(e)}") 