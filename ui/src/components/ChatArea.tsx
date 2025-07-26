import { MessageCircle, Send, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage, Container } from "@/types/container";

interface ChatAreaProps {
  container: Container | null;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isUser
            ? 'bg-chat-user-bg text-chat-user-text ml-4'
            : 'bg-chat-bot-bg text-chat-bot-text mr-4'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        <div className={`text-xs mt-1 opacity-70 ${
          isUser ? 'text-chat-user-text' : 'text-chat-bot-text'
        }`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
      <MessageCircle className="h-16 w-16 text-muted-foreground" />
      <div>
        <h3 className="text-lg font-medium text-foreground">No Container Selected</h3>
        <p className="text-muted-foreground mt-2">
          Select a Docker container from the sidebar to start viewing its logs and chatting.
        </p>
      </div>
    </div>
  );
}

function StoppedContainerState({ container }: { container: Container }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
      <div className="h-16 w-16 rounded-full bg-status-stopped flex items-center justify-center">
        <Square className="h-8 w-8 text-white" />
      </div>
      <div>
        <h3 className="text-lg font-medium text-foreground">Container is not running</h3>
        <p className="text-muted-foreground mt-2">
          The container <span className="font-medium text-foreground">{container.name}</span> is currently stopped. 
          Start the container to enable chat functionality.
        </p>
      </div>
    </div>
  );
}

export function ChatArea({ container, messages, onSendMessage }: ChatAreaProps) {
  const [inputValue, setInputValue] = useState("");
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (inputValue.trim() && container) {
      onSendMessage(inputValue.trim());
      setInputValue("");
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!container) {
    return (
      <div className="flex-1 bg-background">
        <EmptyState />
      </div>
    );
  }

  // Show stopped container state if container is not running
  if (container.status !== 'running') {
    return (
      <div className="flex-1 bg-background">
        <StoppedContainerState container={container} />
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card p-4">
        <div className="flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-status-running"></div>
          <div>
            <h2 className="text-lg font-semibold text-card-foreground">{container.name}</h2>
            <p className="text-sm text-muted-foreground">{container.image}</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>You are now talking to <span className="font-medium text-foreground">{container.name}</span> with id <span className="font-medium text-foreground">{container.id}</span></p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatBubble key={message.id} message={message} />
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t border-border bg-card p-4">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`Send a message to ${container.name}...`}
            className="flex-1"
          />
          <Button onClick={handleSend} disabled={!inputValue.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}