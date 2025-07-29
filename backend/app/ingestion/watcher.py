"""
Docker watcher to monitor container events and manage log streamers.
Reference: https://docker-py.readthedocs.io/en/stable/containers.html
"""
import asyncio
from typing import Dict, Optional

import docker
from app.ingestion.streamer import LogStreamer


class DockerWatcher:
    """Watches Docker events and manages log streamers."""
    
    def __init__(self):
        """Initialize Docker watcher."""
        self.client = docker.from_env()
        self.running = False
        self.streamers: Dict[str, LogStreamer] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}
        self.event_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start watching Docker events and existing containers."""
        self.running = True
        
        # Initialize streamers for containers already running
        await self._initialize_running_containers()
        
        # Launch event monitor as an async task
        self.event_task = asyncio.create_task(self._monitor_events())
        
        print("Docker watcher started")

    async def stop(self):
        """Stop watching Docker events and all streamers."""
        self.running = False
        
        # Cancel event monitor
        if self.event_task:
            self.event_task.cancel()
            try:
                await self.event_task
            except asyncio.CancelledError:
                pass
        
        # Stop and cancel each streamer task
        for container_id, streamer in list(self.streamers.items()):
            # Signal streamer to stop
            await streamer.stop_streaming()
            # Cancel its task
            task = self.stream_tasks.pop(container_id, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del self.streamers[container_id]

        print("Docker watcher stopped")

    async def _monitor_events(self):
        """Monitor Docker events in a background thread and dispatch them."""
        try:
            # Run the blocking Docker events in a thread
            await asyncio.to_thread(self._run_event_monitor)
        except Exception as e:
            print(f"Error in event monitor: {str(e)}")

    def _run_event_monitor(self):
        """Run the blocking Docker events monitor in a thread."""
        try:
            for event in self.client.events(decode=True):
                if not self.running:
                    break
                
                # Process container events
                if event.get('Type') == 'container':
                    # Schedule the event handling on the main event loop
                    asyncio.create_task(self._handle_container_event(event))
                    
        except Exception as e:
            print(f"Error monitoring Docker events: {str(e)}")

    async def _handle_container_event(self, event: Dict):
        """Handle container start/stop events."""
        if not self.running:
            return
            
        try:
            action = event.get('Action')
            container_id = event.get('Actor', {}).get('ID')
            
            if not container_id:
                return
            
            if action == 'start':
                await self._start_container_streamer(container_id)
            elif action in ('stop', 'die'):
                await self._stop_container_streamer(container_id)
                
        except Exception as e:
            print(f"Error handling container event: {str(e)}")

    async def _initialize_running_containers(self):
        """Initialize streamers for currently running containers."""
        try:
            # Run the blocking Docker operation in a thread
            containers = await asyncio.to_thread(self.client.containers.list)
            
            for container in containers:
                await self._start_container_streamer(container.id)
                
        except Exception as e:
            print(f"Error initializing running containers: {str(e)}")

    async def _start_container_streamer(self, container_id: str):
        """Start a log streamer for a container."""
        if container_id in self.streamers:
            return  # Already streaming
            
        try:
            # Check if container is running (run in thread)
            container = await asyncio.to_thread(self.client.containers.get, container_id)
            
            if container.status != 'running':
                return
            
            # Create and start streamer
            streamer = LogStreamer(container_id)
            self.streamers[container_id] = streamer
            
            # Start streaming in background task
            task = asyncio.create_task(streamer.start_streaming())
            self.stream_tasks[container_id] = task
            
            # Add error callback
            task.add_done_callback(
                lambda t: print(f"Streamer task error for {container_id}: {t.exception()}") 
                if t.exception() else None
            )
            
            print(f"Started log streaming for container: {container.name} ({container_id})")
            
        except Exception as e:
            print(f"Error starting streamer for container {container_id}: {str(e)}")

    async def _stop_container_streamer(self, container_id: str):
        """Stop a log streamer for a container."""
        try:
            streamer = self.streamers.get(container_id)
            if not streamer:
                return
            
            # Stop the streamer
            await streamer.stop_streaming()
            
            # Cancel the streaming task
            task = self.stream_tasks.pop(container_id, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            del self.streamers[container_id]
            print(f"Stopped log streaming for container: {container_id}")
            
        except Exception as e:
            print(f"Error stopping streamer for container {container_id}: {str(e)}")

    async def get_active_streamers(self) -> Dict[str, str]:
        """Get list of active streamers with container names."""
        active: Dict[str, str] = {}
        
        for container_id, streamer in self.streamers.items():
            try:
                # Run the blocking Docker operation in a thread
                container = await asyncio.to_thread(self.client.containers.get, container_id)
                active[container_id] = container.name
            except Exception:
                active[container_id] = "unknown"
                
        return active 