import { Container, ChatMessage, ContainerLogs } from "@/types/container";

export const mockContainers: Container[] = [
  {
    id: "container-1",
    name: "web-app",
    image: "nginx:latest",
    status: "running",
    created: "2024-01-15T10:30:00Z",
    ports: ["80:8080", "443:8443"]
  },
  {
    id: "container-2", 
    name: "api-server",
    image: "node:18-alpine",
    status: "running",
    created: "2024-01-15T11:00:00Z",
    ports: ["3000:3000"]
  },
  {
    id: "container-3",
    name: "database",
    image: "postgres:15",
    status: "running", 
    created: "2024-01-15T09:45:00Z",
    ports: ["5432:5432"]
  },
  {
    id: "container-4",
    name: "redis-cache",
    image: "redis:7-alpine",
    status: "paused",
    created: "2024-01-15T12:15:00Z",
    ports: ["6379:6379"]
  },
  {
    id: "container-5",
    name: "worker-queue",
    image: "python:3.11-slim",
    status: "stopped",
    created: "2024-01-15T08:30:00Z"
  }
];

export const mockChatLogs: ContainerLogs[] = [];