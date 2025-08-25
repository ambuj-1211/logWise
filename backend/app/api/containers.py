"""
API routes for Docker container operations.
"""
import asyncio
import json
from typing import AsyncGenerator, List

import docker
from docker.models.containers import Container as DockerContainer
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()

class ContainerInfo(BaseModel):
    """Container information model."""
    id: str
    name: str
    image: str
    status: str
    created: str
    ports: List[str] = []

async def container_event_generator(request: Request) -> AsyncGenerator[str, None]:
    """
    An async generator that yields container information in SSE format.
    """
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)

        for container in containers:
            # Check if the client has disconnected
            if await request.is_disconnected():
                print("Client disconnected. Stopping stream.")
                break

            # Get container info
            container_info = ContainerInfo(
                id=container.id,
                name=container.name,
                image=container.image.tags[0] if container.image.tags else "unknown",
                status=container.status,
                created=container.attrs['Created'][:10] if 'Created' in container.attrs else "unknown"
            )

            # Get port mappings
            if 'Ports' in container.attrs['NetworkSettings']:
                ports_data = container.attrs['NetworkSettings']['Ports']
                if ports_data:
                    port_list = []
                    # The internal container port is the key, value is a list of host mappings
                    for internal_port, host_mappings in ports_data.items():
                        if host_mappings:
                            for mapping in host_mappings:
                                host_ip = mapping.get('HostIp', '0.0.0.0')
                                host_port = mapping.get('HostPort', '')
                                port_list.append(f"{host_ip}:{host_port} -> {internal_port}")
                    container_info.ports = port_list
            
            # Convert Pydantic model to JSON and format for SSE
            json_data = container_info.model_dump_json()
            yield f"data: {json_data}\n\n"
            
            # Small delay to prevent overwhelming the event loop on systems with many containers
            await asyncio.sleep(0.01)

    except Exception as e:
        # Yield an error event for the client to handle
        error_message = {"error": f"Failed to list containers: {str(e)}"}
        import json
        yield f"data: {json.dumps(error_message)}\n\n"
        # We can't raise HTTPException in a generator, so we log it and stop
        print(f"Error streaming container data: {e}")

# def _to_container_info(container: DockerContainer) -> ContainerInfo:
#     """Helper function to convert a Docker container object to our Pydantic model."""
#     # The container object from client.containers.get() is slightly different
#     # from client.containers.list(), so we access attributes safely.
#     attrs = container.attrs
#     image_tag = "unknown"
#     if container.image and container.image.tags:
#         image_tag = container.image.tags[0]

#     port_list = []
#     if attrs and 'NetworkSettings' in attrs and 'Ports' in attrs['NetworkSettings']:
#         ports_data = attrs['NetworkSettings']['Ports']
#         for internal_port, host_mappings in ports_data.items():
#             if host_mappings:
#                 for mapping in host_mappings:
#                     host_ip = mapping.get('HostIp', '0.0.0.0')
#                     host_port = mapping.get('HostPort', '')
#                     port_list.append(f"{host_ip}:{host_port} -> {internal_port}")

#     return ContainerInfo(
#         id=container.id,
#         name=container.name,
#         image=image_tag,
#         status=container.status,
#         created=attrs['Created'][:19].replace("T", " ") if 'Created' in attrs else "unknown",
#         ports=port_list
#     )

# async def container_event_generator(request: Request) -> AsyncGenerator[str, None]:
#     """
#     Sends the initial container list, then streams live Docker events.
#     This version is non-blocking and sends full container info on updates.
#     """
#     client = docker.from_env()

#     # --- Step 1: Send the initial, full list of containers ---
#     try:
#         initial_containers = client.containers.list(all=True)
#         container_list = [_to_container_info(c).model_dump() for c in initial_containers]
        
#         initial_data = {
#             "type": "initial_list",
#             "payload": container_list
#         }
#         yield f"data: {json.dumps(initial_data)}\n\n"
#     except Exception as e:
#         error_data = {"type": "error", "message": f"Failed to get initial list: {str(e)}"}
#         yield f"data: {json.dumps(error_data)}\n\n"
#         return

#     # --- Step 2: Listen for live events in a separate thread ---
#     try:
#         # Use asyncio.to_thread to run the blocking 'client.events' in the background
#         event_stream = await asyncio.to_thread(client.events, decode=True)
        
#         for event in event_stream:
#             if await request.is_disconnected():
#                 print("Client disconnected, stopping event stream.")
#                 break

#             if event.get('Type') == 'container':
#                 status = event.get('status')
                
#                 if status in ['start', 'stop', 'die', 'create']:
#                     # For updates, get the full container object
#                     try:
#                         container_obj = client.containers.get(event['id'])
#                         container_info = _to_container_info(container_obj)
#                         event_data = {
#                             "type": "container_update",
#                             "payload": container_info.model_dump()
#                         }
#                         yield f"data: {json.dumps(event_data)}\n\n"
#                     except docker.errors.NotFound:
#                         # Container might be gone before we can get it, just skip
#                         continue
                
#                 elif status == 'destroy':
#                     # For removal, we only need to send the ID
#                     event_data = {
#                         "type": "container_remove",
#                         "payload": {"id": event['id']}
#                     }
#                     yield f"data: {json.dumps(event_data)}\n\n"
                    
#     except Exception as e:
#         print(f"Error streaming Docker events: {e}")
#         error_data = {"type": "error", "message": f"Error during event streaming: {str(e)}"}
#         yield f"data: {json.dumps(error_data)}\n\n"
        
    
@router.get("/api/containers")
async def list_containers_sse(request: Request):
    """
    List all Docker containers using Server-Sent Events (SSE).
    This streams container data as it becomes available.
    """
    return StreamingResponse(container_event_generator(request), media_type="text/event-stream")


# @router.get("/api/containers", response_model=List[ContainerInfo])
# async def list_containers() -> List[ContainerInfo]:
#     """List all Docker containers."""
#     try:
#         client = docker.from_env()
#         containers = client.containers.list(all=True)
        
#         container_list = []
#         for container in containers:
#             # Get container info
#             container_info = ContainerInfo(
#                 id=container.id,
#                 name=container.name,
#                 image=container.image.tags[0] if container.image.tags else "unknown",
#                 status=container.status,
#                 created=container.attrs['Created'][:10] if 'Created' in container.attrs else "unknown"
#             )
            
#             # Get port mappings
#             if 'Ports' in container.attrs['NetworkSettings']:
#                 ports = container.attrs['NetworkSettings']['Ports']
#                 if ports:
#                     port_list = []
#                     for port_mapping in ports.values():
#                         if port_mapping:
#                             for mapping in port_mapping:
#                                 port_list.append(f"{mapping['HostPort']}:{mapping['HostIp']}")
#                     container_info.ports = port_list
            
#             container_list.append(container_info)
        
#         return container_list
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Failed to list containers: {str(e)}")


@router.get("/api/containers/{container_id}")
async def get_container_info(container_id: str) -> ContainerInfo:
    """Get detailed information about a specific container."""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        container_info = ContainerInfo(
            id=container.id,
            name=container.name,
            image=container.image.tags[0] if container.image.tags else "unknown",
            status=container.status,
            created=container.attrs['Created'][:10] if 'Created' in container.attrs else "unknown"
        )
        
        # Get port mappings
        if 'Ports' in container.attrs['NetworkSettings']:
            ports = container.attrs['NetworkSettings']['Ports']
            if ports:
                port_list = []
                for port_mapping in ports.values():
                    if port_mapping:
                        for mapping in port_mapping:
                            port_list.append(f"{mapping['HostPort']}:{mapping['HostIp']}")
                container_info.ports = port_list
        
        return container_info
        
    except docker.errors.NotFound:
        raise HTTPException(status_code=404, detail="Container not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get container info: {str(e)}")