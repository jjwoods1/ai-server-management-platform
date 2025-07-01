'use client';

import { useState, useEffect } from 'react';

// Define the structure of our messages and plans
type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
  commands?: string[]; // Optional: AI responses can now include commands
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);

  // This hook checks for active agents
  useEffect(() => {
    const fetchActiveAgents = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8001/api/agents/active');
        const data = await res.json();
        setActiveAgentId(data.active_agent_ids?.[0] || null);
      } catch (error) {
        setActiveAgentId(null);
      }
    };
    const interval = setInterval(fetchActiveAgents, 3000);
    return () => clearInterval(interval);
  }, []);

  // This function sends a single command to the agent
  const handleSendCommand = async (command: string, onResult: (result: string) => void) => {
    if (!activeAgentId) return;
    try {
      const res = await fetch('http://127.0.0.1:8001/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command, agent_id: activeAgentId }),
      });
      const data = await res.json();
      if (data.task_id) {
        pollForResult(data.task_id, onResult);
      }
    } catch (error) {
      onResult(`Error sending command: ${command}`);
    }
  };
  
  // This function polls for the result of a single command
  const pollForResult = (taskId: string, onResult: (result: string) => void) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8001/api/command/result/${taskId}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.status === 'complete') {
          clearInterval(interval);
          onResult(data.result);
        }
      } catch (error) { /* Ignore polling errors */ }
    }, 2000);
  };

  // This function executes a multi-step plan
  const handleExecutePlan = async (commands: string[]) => {
    setIsLoading(true);
    for (const command of commands) {
      const systemMessage: Message = { role: 'system', content: `Executing: ${command}` };
      setMessages(prev => [...prev, systemMessage]);
      
      await new Promise<void>(resolve => {
        handleSendCommand(command, (result) => {
          const resultMessage: Message = { role: 'system', content: `✅ Output:\n${result}` };
          setMessages(prev => [...prev, resultMessage]);
          resolve();
        });
      });
    }
    const finalMessage: Message = { role: 'system', content: '🎉 Plan execution complete!' };
    setMessages(prev => [...prev, finalMessage]);
    setIsLoading(false);
  };

  // This is the main function for sending a chat message to the AI
  const handleSendMessage = async () => {
    if (input.trim() === '' || isLoading) return;
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInput('');
    try {
      const response = await fetch('http://127.0.0.1:8001/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: input }),
      });
      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.explanation,
        commands: data.commands, // Attach the commands to the message
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to connect to the backend:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-800 text-white">
      <main className="flex flex-1 flex-col">
        {/* Header */}
        <div className="border-b border-gray-700 p-4 flex justify-between items-center">
          <div className='flex items-center gap-4'>
            <h1 className="text-xl font-bold">AI Server Assistant</h1>
            <div className={`text-xs font-mono p-1 px-2 rounded ${activeAgentId ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
              Agent Status: {activeAgentId ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>

        {/* Message History */}
        <div className="flex-1 space-y-6 overflow-y-auto p-6">
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-start gap-4 ${msg.role === 'user' ? 'justify-end' : ''}`}>
               {msg.role !== 'user' && <div className={`h-8 w-8 flex-shrink-0 rounded-full ${msg.role === 'assistant' ? 'bg-blue-500' : msg.role === 'system' ? 'bg-yellow-500' : ''}`}></div>}
              <div
                className={`max-w-3xl rounded-lg p-4 whitespace-pre-wrap ${
                  msg.role === 'user' ? 'bg-gray-700' :
                  msg.role === 'assistant' ? 'bg-gray-900' : 'bg-yellow-900/50 font-mono text-xs'
                }`}
              >
                <p>{msg.content}</p>
                {/* If the message is from the assistant and has commands, show the button */}
                {msg.role === 'assistant' && msg.commands && msg.commands.length > 0 && (
                  <div className="mt-4 border-t border-gray-700 pt-2">
                    <button
                      onClick={() => handleExecutePlan(msg.commands || [])}
                      disabled={isLoading || !activeAgentId}
                      className="rounded bg-green-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-green-500 disabled:bg-gray-500"
                    >
                      Execute Plan
                    </button>
                  </div>
                )}
              </div>
              {msg.role === 'user' && <div className="h-8 w-8 flex-shrink-0 rounded-full bg-gray-600"></div>}
            </div>
          ))}
          {isLoading && messages[messages.length - 1]?.role === 'user' && (
            <div className="flex items-start gap-4">
              <div className="h-8 w-8 flex-shrink-0 rounded-full bg-blue-500"></div>
              <div className="max-w-lg rounded-lg bg-gray-900 p-4"><p>Assistant is thinking...</p></div>
            </div>
          )}
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-700 bg-gray-900 p-4">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !isLoading) handleSendMessage(); }}
              placeholder="Ask the AI to perform a task..."
              className="w-full rounded-lg border border-gray-600 bg-gray-800 p-3 pr-12 text-sm text-white placeholder-gray-400 focus:border-blue-500 focus:outline-none"
              disabled={isLoading}
            />
            <button
              onClick={handleSendMessage}
              className="absolute inset-y-0 right-0 flex items-center justify-center rounded-r-lg bg-blue-600 px-4 text-white hover:bg-blue-700 disabled:bg-gray-500"
              disabled={isLoading}
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}