import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Sidebar({ chats, activeChat, onSelectChat, onNewChat, onDeleteChat }) {
  const { user, logout } = useAuth()
  const [hoveredChat, setHoveredChat] = useState(null)

  return (
    <div className="w-64 h-screen bg-[#0d0d14] border-r border-white/[0.06] flex flex-col shrink-0">

      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-4">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <span className="font-bold text-white text-sm">LLM Chat</span>
            <p className="text-gray-600 text-xs">AI Assistant</p>
          </div>
        </div>

        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-sm font-semibold px-3 py-2.5 rounded-xl transition-all duration-200 shadow-lg shadow-violet-500/20 hover:shadow-violet-500/30"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Chat List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {chats.length === 0 ? (
          <div className="flex flex-col items-center justify-center mt-12 px-4 text-center">
            <div className="w-10 h-10 rounded-2xl bg-gray-800/60 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <p className="text-gray-500 text-xs">No chats yet</p>
            <p className="text-gray-600 text-xs mt-0.5">Start a new conversation</p>
          </div>
        ) : (
          <>
            <p className="text-gray-600 text-xs font-medium px-3 py-1.5 uppercase tracking-wider">Recent</p>
            {chats.map(chat => (
              <div
                key={chat.id}
                onClick={() => onSelectChat(chat)}
                onMouseEnter={() => setHoveredChat(chat.id)}
                onMouseLeave={() => setHoveredChat(null)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer transition-all duration-150 ${
                  activeChat?.id === chat.id
                    ? 'bg-violet-600/15 border border-violet-500/20 text-white'
                    : 'text-gray-400 hover:bg-gray-800/60 hover:text-white border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  {/* Active indicator */}
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 transition-all ${
                    activeChat?.id === chat.id ? 'bg-violet-400' : 'bg-transparent'
                  }`} />
                  <span className="text-sm truncate">{chat.title}</span>
                </div>

                {/* Delete button */}
                {hoveredChat === chat.id && (
                  <button
                    onClick={e => { e.stopPropagation(); onDeleteChat(chat.id) }}
                    className="shrink-0 p-1 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-all duration-150"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                )}
              </div>
            ))}
          </>
        )}
      </div>

      {/* User Profile */}
      <div className="p-3 border-t border-white/[0.06]">
        <div className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-gray-800/40 transition group">
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-md shadow-violet-500/20">
            <span className="text-white text-xs font-bold">
              {user?.username?.[0]?.toUpperCase()}
            </span>
          </div>

          {/* Username + email */}
          <div className="min-w-0 flex-1">
            <p className="text-sm text-white font-medium truncate">{user?.username}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>

          {/* Logout */}
          <button
            onClick={logout}
            className="shrink-0 p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-400/10 transition-all duration-150"
            title="Logout"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}