import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export default function MessageBubble({ message }) {
  const [copied, setCopied] = useState(false)

  // ✅ Guard first — before ANY property access
  if (!message || !message.role) return null
  if (message.role === 'assistant' && !message.content) return null

  const isUser = message.role === 'user'

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className={`flex gap-3 px-2 ${isUser ? 'justify-end' : 'justify-start'}`}>

      {/* AI Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-xs text-white font-bold shrink-0 shadow-lg shadow-violet-500/20">
          AI
        </div>
      )}

      {/* Bubble */}
      <div className={`group relative max-w-[78%] ${
        isUser
          ? 'bg-gradient-to-br from-violet-600 to-indigo-600 text-white rounded-2xl rounded-tr-sm shadow-lg shadow-violet-500/20'
          : 'bg-gray-800/60 border border-white/[0.06] text-gray-100 rounded-2xl rounded-tl-sm'
      } px-4 py-3`}>

        {/* Copy button */}
        <button
          onClick={handleCopy}
          className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-200 p-1.5 rounded-lg bg-gray-700 border border-white/[0.08] hover:bg-gray-600 text-gray-300 shadow-lg"
          title="Copy message"
        >
          {copied ? (
            <svg className="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          )}
        </button>

        {/* Content */}
        <div className={`prose prose-sm max-w-none ${
          isUser
            ? 'prose-invert [&_*]:text-white [&_code]:bg-white/20 [&_code]:text-white'
            : 'prose-invert [&_code]:bg-gray-900 [&_code]:text-violet-300 [&_pre]:bg-gray-900 [&_pre]:border [&_pre]:border-white/[0.06]'
        }`}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-xs text-white font-bold shrink-0 shadow-lg shadow-violet-500/20">
          You
        </div>
      )}
    </div>
  )
}