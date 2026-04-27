import { Component } from 'react'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Caught error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
          <div className="text-center">
            <h2 className="text-xl font-bold text-white mb-2">Something went wrong</h2>
            <p className="text-gray-400 mb-4">Please try refreshing the page</p>
            <button
              onClick={() => window.location.reload()}
              className="bg-violet-600 hover:bg-violet-500 text-white px-4 py-2 rounded-lg"
            >
              Refresh
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}