import { ChatArea } from "@/components/ChatArea";
import { ContainerSidebar } from "@/components/ContainerSidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { mockChatLogs, mockContainers } from "@/data/mockData";
import { ChatMessage, Container } from "@/types/container";
import { useState } from "react";

const Index = () => {
  const [selectedContainer, setSelectedContainer] = useState<Container | null>(null);
  const [chatLogs, setChatLogs] = useState(mockChatLogs);

  const handleContainerSelect = (container: Container) => {
    setSelectedContainer(container);
  };

  const handleSendMessage = (messageContent: string) => {
    if (!selectedContainer) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      type: 'user',
      content: messageContent,
      timestamp: new Date()
    };

    const botMessage: ChatMessage = {
      id: `msg-${Date.now()}-bot`,
      type: 'bot',
      content: `Received: "${messageContent}"\n\nThis is a mock response. In a real application, this would be processed by your backend and return actual container logs or execute commands.`,
      timestamp: new Date(Date.now() + 1000)
    };

    setChatLogs(prev => {
      const existingLogIndex = prev.findIndex(log => log.containerId === selectedContainer.id);
      
      if (existingLogIndex >= 0) {
        const updatedLogs = [...prev];
        updatedLogs[existingLogIndex] = {
          ...updatedLogs[existingLogIndex],
          messages: [...updatedLogs[existingLogIndex].messages, userMessage, botMessage]
        };
        return updatedLogs;
      } else {
        return [...prev, {
          containerId: selectedContainer.id,
          messages: [userMessage, botMessage]
        }];
      }
    });
  };

  const currentMessages = selectedContainer 
    ? chatLogs.find(log => log.containerId === selectedContainer.id)?.messages || []
    : [];

  return (
    <div className="min-h-screen flex w-full bg-background">
      <ContainerSidebar
        containers={mockContainers}
        selectedContainer={selectedContainer}
        onContainerSelect={handleContainerSelect}
      />
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 flex items-center justify-between border-b border-border bg-card px-4">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold text-card-foreground">
              logWise
            </h1>
          </div>
          <ThemeToggle />
        </header>

        {/* Main Content */}
        <ChatArea
          container={selectedContainer}
          messages={currentMessages}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
};

export default Index;