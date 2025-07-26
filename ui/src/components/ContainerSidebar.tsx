import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Container } from "@/types/container";
import { Calendar, ChevronLeft, ChevronRight, Container as DockerIcon, Image, Network, Pause, Play, Square } from "lucide-react";
import { useState } from "react";

interface ContainerSidebarProps {
  containers: Container[];
  selectedContainer: Container | null;
  onContainerSelect: (container: Container) => void;
}

const getStatusIcon = (status: Container['status']) => {
  switch (status) {
    case 'running':
      return <Play className="h-3 w-3 text-status-running" />;
    case 'stopped':
      return <Square className="h-3 w-3 text-status-stopped" />;
    case 'paused':
      return <Pause className="h-3 w-3 text-status-paused" />;
    default:
      return <Square className="h-3 w-3" />;
  }
};

const getStatusColor = (status: Container['status']) => {
  switch (status) {
    case 'running':
      return 'bg-status-running text-white';
    case 'stopped':
      return 'bg-status-stopped text-white';
    case 'paused':
      return 'bg-status-paused text-white';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

export function ContainerSidebar({ containers, selectedContainer, onContainerSelect }: ContainerSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const runningContainers = containers.filter(container => container.status === 'running');
  const stoppedContainers = containers.filter(container => container.status !== 'running');

  const renderContainerList = (containerList: Container[], groupName: string) => (
    <div className="mb-6">
      <h3 className="px-4 py-2 text-sm font-medium text-muted-foreground">
        {!isCollapsed && groupName}
      </h3>
      <div className="space-y-1 px-2">
        {containerList.map((container) => (
          <button
            key={container.id}
            onClick={() => onContainerSelect(container)}
            className={`w-full ${isCollapsed ? 'p-2 justify-center' : 'p-3'} text-left hover:bg-accent rounded-lg transition-colors ${
              selectedContainer?.id === container.id 
                ? 'bg-accent text-accent-foreground' 
                : ''
            }`}
          >
            {isCollapsed ? (
              <div className="flex justify-center">
                {getStatusIcon(container.status)}
              </div>
            ) : (
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-3">
                  {getStatusIcon(container.status)}
                  <div>
                    <div className="font-medium text-sm">{container.name}</div>
                    <div className="text-xs text-muted-foreground">{container.image}</div>
                  </div>
                </div>
                <Badge 
                  className={`text-xs ${getStatusColor(container.status)}`}
                >
                  {container.status}
                </Badge>
              </div>
            )}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="relative">
      <div className={`${isCollapsed ? 'w-16' : 'w-80'} border-r border-border bg-card transition-all duration-200 h-screen flex flex-col`}>
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className={`flex items-center gap-2 ${isCollapsed ? 'justify-center' : ''}`}>
            <DockerIcon className="h-6 w-6 text-primary" />
            {!isCollapsed && <h2 className="text-lg font-semibold">Containers</h2>}
          </div>
        </div>

        {/* Selected Container Details */}
        {selectedContainer && !isCollapsed && (
          <div className="p-4 border-b border-border">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  {getStatusIcon(selectedContainer.status)}
                  {selectedContainer.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <Image className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">{selectedContainer.image}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-3 w-3 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    {new Date(selectedContainer.created).toLocaleDateString()}
                  </span>
                </div>
                {selectedContainer.ports && selectedContainer.ports.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Network className="h-3 w-3 text-muted-foreground" />
                    <span className="text-muted-foreground">
                      {selectedContainer.ports.join(', ')}
                    </span>
                  </div>
                )}
                <Badge 
                  className={`text-xs ${getStatusColor(selectedContainer.status)}`}
                >
                  {selectedContainer.status}
                </Badge>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Container Lists */}
        <div className="flex-1 overflow-y-auto py-4">
          {renderContainerList(runningContainers, 'Running Containers')}
          {renderContainerList(stoppedContainers, 'Stopped Containers')}
        </div>
      </div>

      {/* Collapse/Expand Arrow Button */}
      <Button
        variant="outline"
        size="icon"
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute -right-4 top-1/2 transform -translate-y-1/2 h-8 w-8 rounded-full border-2 bg-background hover:bg-accent z-10"
      >
        {isCollapsed ? (
          <ChevronRight className="h-4 w-4" />
        ) : (
          <ChevronLeft className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}