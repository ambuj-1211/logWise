"""
API routes for Docker container operations.
"""
from typing import List

import docker
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ContainerInfo(BaseModel):
    """Container information model."""
    id: str
    name: str
    image: str
    status: str
    state: str
    created: str
    ports: List[str] = []


@router.get("/api/containers", response_model=List[ContainerInfo])
async def list_containers() -> List[ContainerInfo]:
    """List all Docker containers."""
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        
        container_list = []
        for container in containers:
            # Get container info
            container_info = ContainerInfo(
                id=container.id,
                name=container.name,
                image=container.image.tags[0] if container.image.tags else "unknown",
                status=container.status,
                state=container.status,
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
            
            container_list.append(container_info)
        
        return container_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list containers: {str(e)}")


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
            state=container.status,
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