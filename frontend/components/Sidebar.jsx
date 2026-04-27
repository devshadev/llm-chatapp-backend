import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Sidebar({ chats, activeChat, onSelectChat, onNewChat, onDeleteChat }) {
  const { user, logout } = useAuth()
  const [hoveredChat, setHoveredChat] = useState(null)
  const [chatToDelete, setChatToDelete] = useState(null) // holds the chat pending deletion

  const handleDeleteClick = (e, chat) => {
    e.stopPropagation()
    setChatToDelete(chat) // open modal
  }

  const handleConfirmDelete = () => {
    onDeleteChat(chatToDelete.id)
    setChatToDelete(null) // close modal
  }

  const handleCancelDelete = () => {
    setChatToDelete(null) // close modal
  }

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
                  <div className={`w-1.5 h-1.5 rounded-full shrink-0 transition-all ${
                    activeChat?.id === chat.id ? 'bg-violet-400' : 'bg-transparent'
                  }`} />
                  <span className="text-sm truncate">{chat.title}</span>
                </div>

                {/* Delete button — now opens modal instead of deleting directly */}
                {hoveredChat === chat.id && (
                  <button
                    onClick={e => handleDeleteClick(e, chat)}
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
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-md shadow-violet-500/20">
            <span className="text-white text-xs font-bold">
              {user?.username?.[0]?.toUpperCase()}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm text-white font-medium truncate">{user?.username}</p>
            <p className="text-xs text-gray-500 truncate">{user?.email}</p>
          </div>
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

      {/* Delete Confirmation Modal */}
      {chatToDelete && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={handleCancelDelete} // clicking backdrop closes modal
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

          {/* Modal */}
          <div
            className="relative bg-[#13131f] border border-white/[0.08] rounded-2xl p-6 w-full max-w-sm shadow-2xl shadow-black/50"
            onClick={e => e.stopPropagation()} // prevent backdrop click when clicking modal
          >
            {/* Icon */}
            <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>

            {/* Text */}
            <h3 className="text-white font-semibold text-center text-base mb-1">
              Delete Chat
            </h3>
            <p className="text-gray-400 text-sm text-center mb-1">
              Are you sure you want to delete
            </p>
            <p className="text-violet-400 text-sm text-center font-medium mb-6 truncate px-4">
              "{chatToDelete.title}"
            </p>
            <p className="text-gray-600 text-xs text-center mb-6">
              This action cannot be undone.
            </p>

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={handleCancelDelete}
                className="flex-1 bg-gray-800 hover:bg-gray-700 border border-white/[0.06] text-gray-300 text-sm font-medium py-2.5 rounded-xl transition-all duration-150"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                className="flex-1 bg-red-500/90 hover:bg-red-500 text-white text-sm font-medium py-2.5 rounded-xl transition-all duration-150 shadow-lg shadow-red-500/20"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}