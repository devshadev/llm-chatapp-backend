import { useState, useEffect, useRef } from 'react'
import Sidebar from '../components/Sidebar'
import MessageBubble from '../components/MessageBubble'
import api from '../api'

export default function Chat() {
  const [chats, setChats] = useState([])
  const [activeChat, setActiveChat] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingChats, setLoadingChats] = useState(true)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    try {
      const res = await api.get('/chats/')
      setChats(res.data)
    } catch (err) {
      console.error('Failed to load chats', err)
    }
    setLoadingChats(false)
  }

  const handleSelectChat = async (chat) => {
    setActiveChat(chat)
    try {
      const res = await api.get(`/chats/${chat.id}`)
      setMessages(res.data.messages)
    } catch (err) {
      console.error('Failed to load messages', err)
    }
  }

  const handleNewChat = async () => {
    try {
      const res = await api.post('/chats/', { title: 'New Chat' })
      setChats(prev => [res.data, ...prev])
      setActiveChat(res.data)
      setMessages([])
    } catch (err) {
      console.error('Failed to create chat', err)
    }
  }

  const handleDeleteChat = async (chatId) => {
    try {
      await api.delete(`/chats/${chatId}`)
      setChats(prev => prev.filter(c => c.id !== chatId))
      if (activeChat?.id === chatId) {
        setActiveChat(null)
        setMessages([])
      }
    } catch (err) {
      console.error('Failed to delete chat', err)
    }
  }

  // ✅ Updated handleSend with streaming
  const handleSend = async () => {
    if (!input.trim() || !activeChat || loading) return

    const userMessage = { role: 'user', content: input, id: Date.now() }
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)

    // Update chat title from first message
    if (messages.length === 0) {
      const newTitle = currentInput.slice(0, 40)
      await api.patch(`/chats/${activeChat.id}`, { title: newTitle })
      setChats(prev => prev.map(c =>
        c.id === activeChat.id ? { ...c, title: newTitle } : c
      ))
    }

    // Add empty assistant message to fill in as tokens arrive
    const assistantMsgId = Date.now() + 1
    setMessages(prev => [...prev, { role: 'assistant', content: '', id: assistantMsgId }])

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `http://localhost:8000/chats/${activeChat.id}/messages/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ content: currentInput })
        }
      )

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.token) {
                // Append each token to the assistant message
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: msg.content + data.token }
                    : msg
                ))
              }
            } catch { }
          }
        }
      }
    } catch (err) {
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMsgId
          ? { ...msg, content: 'Sorry, something went wrong. Please try again.' }
          : msg
      ))
    }
    setLoading(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <Sidebar
        chats={chats}
        activeChat={activeChat}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      <div className="flex-1 flex flex-col">
        {activeChat ? (
          <>
            <div className="px-6 py-4 border-b border-gray-800 bg-gray-900">
              <h2 className="font-medium text-white truncate">{activeChat.title}</h2>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-12 h-12 rounded-2xl bg-violet-600/20 flex items-center justify-center mb-4">
                    <svg className="w-6 h-6 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <p className="text-gray-400 font-medium">Start the conversation</p>
                  <p className="text-gray-600 text-sm mt-1">Ask me anything!</p>
                </div>
              )}
              {messages.map((msg, i) => (
                <MessageBubble key={msg.id || i} message={msg} />
              ))}
              {/* Show typing indicator only when loading but assistant message is empty */}
              {loading && messages[messages.length - 1]?.content === '' && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs text-gray-300">AI</div>
                  <div className="bg-gray-800 rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="px-6 py-4 border-t border-gray-800 bg-gray-900">
              <div className="flex gap-3 items-end">
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Message... (Enter to send, Shift+Enter for new line)"
                  rows={1}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition resize-none text-sm"
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  className="bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white p-3 rounded-xl transition shrink-0"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-3xl bg-violet-600/20 flex items-center justify-center mb-6">
              <svg className="w-8 h-8 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">How can I help you today?</h2>
            <p className="text-gray-400 mb-8">Start a new chat or select an existing one</p>
            <button
              onClick={handleNewChat}
              className="bg-violet-600 hover:bg-violet-500 text-white font-medium px-6 py-3 rounded-xl transition"
            >
              Start New Chat
            </button>
          </div>
        )}
      </div>
    </div>
  )
}