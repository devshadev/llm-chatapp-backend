import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import MessageBubble from '../components/MessageBubble'
import api from '../api'

export default function Chat() {
  const { chatId } = useParams()
  const navigate = useNavigate()
  const [chats, setChats] = useState([])
  const [activeChat, setActiveChat] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingChats, setLoadingChats] = useState(true)
  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    loadChats()
  }, [])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 160) + 'px'
    }
  }, [input])

  // When URL has a chatId and chats are loaded, open that chat
  useEffect(() => {
    if (chatId && chats.length > 0) {
      const found = chats.find(c => c.id === chatId)
      if (found) handleSelectChat(found)
    }
  }, [chatId, chats])

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
    navigate(`/chat/${chat.id}`)
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
      navigate(`/chat/${res.data.id}`)
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
        navigate('/')
      }
    } catch (err) {
      console.error('Failed to delete chat', err)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !activeChat || loading) return

    const userMessage = { role: 'user', content: input, id: Date.now() }
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setLoading(true)

    if (messages.length === 0) {
      const newTitle = currentInput.slice(0, 40)
      await api.patch(`/chats/${activeChat.id}`, { title: newTitle })
      setChats(prev => prev.map(c =>
        c.id === activeChat.id ? { ...c, title: newTitle } : c
      ))
    }

    const assistantMsgId = Date.now() + 1
    setMessages(prev => [...prev, { role: 'assistant', content: '', id: assistantMsgId }])

    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/chats/${activeChat.id}/messages/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          credentials: 'include',
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
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? { ...msg, content: msg.content + data.token }
                    : msg
                ))
              }
              if (data.done) {
                setMessages(prev => prev.map(msg =>
                  msg.id === assistantMsgId
                    ? data.assistant_message
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
    <div className="flex h-screen bg-[#0a0a0f]">
      <Sidebar
        chats={chats}
        activeChat={activeChat}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {activeChat ? (
          <>
            {/* Header */}
            <div className="px-6 py-4 border-b border-white/[0.06] bg-[#0d0d14]/80 backdrop-blur-xl flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shrink-0">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div className="min-w-0">
                <h2 className="font-semibold text-white text-sm truncate">{activeChat.title}</h2>
                <p className="text-xs text-gray-500">AI Assistant</p>
              </div>
              <div className="ml-auto flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs text-gray-500">Online</span>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-2">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 border border-violet-500/20 flex items-center justify-center mb-4">
                    <svg className="w-7 h-7 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <p className="text-white font-semibold text-lg">Start the conversation</p>
                  <p className="text-gray-500 text-sm mt-1 mb-6">Ask anything — I'm here to help</p>
                </div>
              )}

              {messages.map((msg, i) => (
                <MessageBubble key={msg.id || i} message={msg} />
              ))}

              {/* Typing indicator */}
              {loading && messages[messages.length - 1]?.content === '' && (
                <div className="flex gap-3 px-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-xs text-white font-bold shrink-0">
                    AI
                  </div>
                  <div className="bg-gray-800/60 border border-white/[0.06] rounded-2xl rounded-tl-sm px-4 py-3">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="px-4 pb-4 pt-2 border-t border-white/[0.06] bg-[#0d0d14]/80 backdrop-blur-xl">
              <div className="max-w-3xl mx-auto">
                <div className="relative bg-gray-800/60 border border-white/[0.08] hover:border-white/[0.12] focus-within:border-violet-500/50 focus-within:ring-2 focus-within:ring-violet-500/10 rounded-2xl transition-all duration-200">
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message AI Assistant..."
                    rows={1}
                    className="w-full bg-transparent px-4 pt-3.5 pb-3 pr-14 text-white text-sm placeholder-gray-500 focus:outline-none resize-none leading-relaxed"
                    style={{ maxHeight: '160px' }}
                  />
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    className="absolute right-2.5 bottom-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-30 disabled:cursor-not-allowed text-white p-2 rounded-xl transition-all duration-200 shadow-lg shadow-violet-500/20"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  </button>
                </div>
                <p className="text-center text-gray-600 text-xs mt-2">
                  Press <kbd className="bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded text-xs">Enter</kbd> to send · <kbd className="bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded text-xs">Shift+Enter</kbd> for new line
                </p>
              </div>
            </div>
          </>
        ) : (
          /* Welcome screen */
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 relative overflow-hidden">
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-violet-600/5 rounded-full blur-[100px] pointer-events-none" />
            <div className="relative z-10">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-violet-500/20 to-indigo-600/20 border border-violet-500/20 flex items-center justify-center mb-6 mx-auto">
                <svg className="w-10 h-10 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h2 className="text-3xl font-bold text-white mb-2 tracking-tight">
                How can I help you today?
              </h2>
              <p className="text-gray-400 mb-10 text-sm">
                Select a chat from the sidebar or start a new one
              </p>
              <button
                onClick={handleNewChat}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold px-8 py-3 rounded-2xl transition-all duration-200 shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40 text-sm"
              >
                Start New Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}