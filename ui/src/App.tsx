import { useState } from 'react';

function App() {
  const [messages, setMessages] = useState<{ sender: 'user' | 'bot', text: string }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { sender: 'user', text: input }]);
    setLoading(true);
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, containerId: 'your_container_id' }) // Replace with actual containerId logic
      });
      const data = await res.json();
      setMessages((msgs) => [...msgs, { sender: 'bot', text: data.response || data.error || 'No response' }]);
    } catch {
      setMessages((msgs) => [...msgs, { sender: 'bot', text: 'Error contacting backend' }]);
    }
    setInput('');
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h2>Simple Docker Chat</h2>
      <div style={{ border: '1px solid #ccc', minHeight: 200, margin: '1rem 0', padding: 8 }}>
        {messages.length === 0 && <div style={{ color: '#888' }}>No messages yet.</div>}
        {messages.map((msg, i) => (
          <div key={i} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
            <b>{msg.sender === 'user' ? 'You' : 'Bot'}:</b> {msg.text}
          </div>
        ))}
        {loading && <div style={{ color: '#888' }}>Bot is thinking...</div>}
      </div>
      <form onSubmit={sendMessage} style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type your message..."
          style={{ flex: 1 }}
          disabled={loading}
        />
        <button type="submit" disabled={!input.trim() || loading}>Send</button>
      </form>
    </div>
  );
}

export default App;
