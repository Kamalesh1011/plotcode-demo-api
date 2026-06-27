import { useState, useRef, useEffect, useCallback } from 'react';
import { sendChat } from '../api';

export default function ChatWidget({ currentPage }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Hi! I'm Plotcode Assistant. I have access to your live dashboard data. Ask me things like:\n\n• How many requests are approved?\n• What's the status of REQ-2025-0001?\n• How many CI failures are there?\n• Which requests need attention?\n• What's the average AI confidence?" }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages, open]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput('');
    setMessages(m => [...m, { role: 'user', text: userMsg }]);
    setLoading(true);

    const result = await sendChat(userMsg, { page: currentPage });
    if (result?.response) {
      setMessages(m => [...m, { role: 'assistant', text: result.response }]);
    } else {
      setMessages(m => [...m, { role: 'assistant', text: "Sorry, I couldn't process that. Make sure the backend is running." }]);
    }
    setLoading(false);
  }, [input, loading, currentPage]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel">
          <div className="chat-header">
            <div className="chat-title">
              <span style={{ fontSize: 18 }}>🤖</span>
              Plotcode Assistant
            </div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>
          <div className="chat-messages" ref={messagesRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg ${m.role}`}>
                {m.text}
              </div>
            ))}
            {loading && <div className="chat-typing">Assistant is typing…</div>}
          </div>
          <div className="chat-input-area">
            <input
              className="chat-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything…"
              disabled={loading}
            />
            <button className="chat-send" onClick={handleSend} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}
      <button className="chat-fab" onClick={() => setOpen(o => !o)} title="AI Assistant">
        {open ? '✕' : '💬'}
      </button>
    </div>
  );
}
