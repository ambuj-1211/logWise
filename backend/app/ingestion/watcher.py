"""
Docker watcher to monitor container events and manage log streamers.
Reference: https://docker-py.readthedocs.io/en/stable/containers.html
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional

import docker
from app.ingestion.streamer import LogStreamer

# Set up logging
logger = logging.getLogger(__name__)


class DockerWatcher:
    """Docker watcher with better monitoring and management."""
        
    def __init__(self):
        """Initialize Docker watcher."""
        self.client = docker.from_env()
        self.running = False
        self.streamers: Dict[str, LogStreamer] = {}
        self.stream_tasks: Dict[str, asyncio.Task] = {}
        self.event_task: Optional[asyncio.Task] = None
        
        # Monitoring statistics
        self.stats = {
            "containers_monitored": 0,
            "total_events_processed": 0,
            "start_events": 0,
            "stop_events": 0,
            "error_events": 0,
            "watcher_start_time": None
        }



    async def start(self):
        """Start watching of Docker events and existing containers."""
        self.running = True
        self.stats["watcher_start_time"] = asyncio.get_event_loop().time()
        logger.info("🚀 Starting Docker watcher...")
        # Initialize streamers for containers already running
        await self._initialize_running_containers()
        # Launch event monitor as an async task
        self.event_task = asyncio.create_task(self._monitor_events())
        logger.info("✅ Docker watcher started successfully")


    async def stop(self):
        """Stop watching Docker events and all streamers."""
        logger.info("🛑 Stopping Docker watcher...")
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
            logger.info(f"🛑 Stopping streamer for container: {container_id}")
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

        logger.info("✅ Docker watcher stopped")



    async def _monitor_events(self):
        """Monitoring of Docker events in a background thread."""
        try:
            # Run the blocking Docker events in a thread
            await asyncio.to_thread(self._run_event_monitor)
        except Exception as e:
            logger.error(f"❌ Error in event monitor: {str(e)}")



    def _run_event_monitor(self):
        """Run the blocking Docker events monitor in a thread."""
        try:
            logger.info("📡 Starting Docker event monitoring...")
            
            for event in self.client.events(decode=True):
                if not self.running:
                    break
                
                # Process container events
                if event.get('Type') == 'container':
                    # Schedule the event handling on the main event loop
                    asyncio.create_task(self._handle_container_event(event))
                    self.stats["total_events_processed"] += 1
                    
        except Exception as e:
            logger.error(f"❌ Error monitoring Docker events: {str(e)}")



    async def _handle_container_event(self, event: Dict):
        """Handling of container start/stop events."""
        if not self.running:
            return
            
        try:
            action = event.get('Action')
            container_id = event.get('Actor', {}).get('ID')
            
            if not container_id:
                return
            
            logger.info(f"📦 Container event: {action} for container {container_id}")
            
            if action == 'start':
                await self._start_container_streamer(container_id)
                self.stats["start_events"] += 1
            elif action in ('stop', 'die'):
                await self._stop_container_streamer(container_id)
                self.stats["stop_events"] += 1
            else:
                # Log other events for debugging
                logger.debug(f"📦 Other container event: {action} for {container_id}")
                
        except Exception as e:
            logger.error(f"❌ Error handling container event: {str(e)}")
            self.stats["error_events"] += 1



    async def _initialize_running_containers(self):
        """Initialize streamers for currently running containers."""
        try:
            logger.info("🔍 Initializing streamers for running containers...")
            
            # Get all running containers.
            containers = await asyncio.to_thread(self.client.containers.list)
            
            logger.info(f"📊 Found {len(containers)} running containers")
            
            for container in containers:
                await self._start_container_streamer(container.id)
                
            logger.info(f"✅ Initialized streamers for {len(containers)} containers")
                
        except Exception as e:
            logger.error(f"❌ Error initializing running containers: {str(e)}")



    async def _start_container_streamer(self, container_id: str):
        """Start log streamer for a container."""
        if container_id in self.streamers:
            logger.info(f"ℹ️  Streamer already exists for container: {container_id}")
            return  # Already streaming
            
        try:
            # Check if container is running (run in thread)
            container = await asyncio.to_thread(self.client.containers.get, container_id)
            if container.status != 'running':
                logger.info(f"ℹ️  Container {container_id} is not running (status: {container.status})")
                return
            
            # Create and start streamer
            streamer = LogStreamer(container_id)
            self.streamers[container_id] = streamer
            
            # Start streaming in background task
            task = asyncio.create_task(streamer.start_streaming())
            self.stream_tasks[container_id] = task
            
            # Add error callback
            task.add_done_callback(
                lambda t: self._handle_streamer_error(container_id, t)
            )
            
            self.stats["containers_monitored"] += 1
            
            logger.info(f"✅ Started log streaming for container: {container.name} ({container_id})")
            
        except Exception as e:
            logger.error(f"❌ Error starting streamer for container {container_id}: {str(e)}")



    def _handle_streamer_error(self, container_id: str, task: asyncio.Task):
        """Handle streamer task errors."""
        if task.exception():
            logger.error(f"❌ Streamer task error for {container_id}: {task.exception()}")
            # Remove from active streamers
            if container_id in self.streamers:
                del self.streamers[container_id]
            if container_id in self.stream_tasks:
                del self.stream_tasks[container_id]



    async def _stop_container_streamer(self, container_id: str):
        """Stop log streamer for a container."""
        try:
            streamer = self.streamers.get(container_id)
            if not streamer:
                logger.info(f"ℹ️  No streamer found for container: {container_id}")
                return
            
            logger.info(f"🛑 Stopping streamer for container: {container_id}")
            
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
            
            self.stats["containers_monitored"] = max(0, self.stats["containers_monitored"] - 1)
            
            logger.info(f"✅ Stopped log streaming for container: {container_id}")
            
        except Exception as e:
            logger.error(f"❌ Error stopping streamer for container {container_id}: {str(e)}")



    async def get_active_streamers(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about active streamers."""
        active: Dict[str, Dict[str, Any]] = {}
        
        for container_id, streamer in self.streamers.items():
            try:
                # Run the blocking Docker operation in a thread
                container = await asyncio.to_thread(self.client.containers.get, container_id)
                
                # Get streamer statistics
                streamer_stats = streamer.get_streaming_stats()
                
                active[container_id] = {
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "streamer_stats": streamer_stats
                }
            except Exception as e:
                logger.error(f"❌ Error getting streamer info for {container_id}: {str(e)}")
                active[container_id] = {
                    "name": "unknown",
                    "status": "unknown",
                    "image": "unknown",
                    "streamer_stats": streamer.get_streaming_stats()
                }
                
        return active
    
    
    
    def get_watcher_stats(self) -> Dict[str, Any]:
        """Get comprehensive watcher statistics."""
        runtime = 0
        if self.stats["watcher_start_time"]:
            runtime = asyncio.get_event_loop().time() - self.stats["watcher_start_time"]
        
        return {
            "running": self.running,
            "active_streamers": len(self.streamers),
            "runtime_seconds": runtime,
            "stats": self.stats.copy()
        }



    async def get_all_container_info(self) -> List[Dict[str, Any]]:
        """Get information about all containers (running and stopped)."""
        try:
            # Get all containers
            containers = await asyncio.to_thread(self.client.containers.list, all=True)
            
            container_info = []
            for container in containers:
                info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                    "has_streamer": container.id in self.streamers,
                    "streamer_running": container.id in self.stream_tasks
                }
                container_info.append(info)
            
            return container_info
            
        except Exception as e:
            logger.error(f"❌ Error getting container info: {str(e)}")
            return []



    async def restart_streamer(self, container_id: str) -> bool:
        """Restart streamer for a specific container."""
        try:
            logger.info(f"🔄 Restarting streamer for container: {container_id}")
            
            # Stop existing streamer if running
            await self._stop_container_streamer(container_id)
            
            # Start new streamer
            await self._start_container_streamer(container_id)
            
            logger.info(f"✅ Successfully restarted streamer for container: {container_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restarting streamer for container {container_id}: {str(e)}")
            return False


# Global Watcher instance
docker_watcher = DockerWatcher()