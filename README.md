# LLM Chat App

A ChatGPT-like application built with FastAPI, MongoDB, Redis, and React.

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** MongoDB Atlas
- **Cache:** Redis
- **Auth:** JWT + GitHub OAuth
- **LLM:** Mistral AI API
- **Frontend:** React + Tailwind CSS

## Architecture

SPA (Single Page Application) → MCS pattern on backend:
- **Models** — MongoDB document shapes (Pydantic)
- **Controllers** — FastAPI route handlers
- **Services** — Business logic layer

## How JWT + Redis Work Together

1. On login → access token (30 min) + refresh token (30 days) created
2. Access token returned in response body → stored in localStorage
3. Refresh token stored in Redis with 30 day TTL → sent as HTTP-only cookie
4. When access token expires → frontend calls `/auth/refresh` → Redis validates refresh token → new access token issued
5. On logout → refresh token deleted from Redis

## Prerequisites

- Python 3.11+
- Node.js 18+
- WSL2 with Redis (Windows) or Redis installed natively
- MongoDB Atlas account (free tier)
- Mistral AI API key (free tier)
- GitHub OAuth App

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd llm-chat-app
```

### 2. Backend Setup
```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/llm_chat
DATABASE_NAME=llm_chat
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
REDIS_HOST=localhost
REDIS_PORT=6379
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
MISTRAL_API_KEY=your-mistral-api-key
```

### 4. GitHub OAuth App Setup
1. Go to github.com/settings/developers
2. Create new OAuth App
3. Set Homepage URL: `http://localhost:8000`
4. Set Callback URL: `http://localhost:8000/auth/github/callback`
5. Copy Client ID and Secret to `.env`

### 5. Start Redis (Windows)
```bash
# In WSL2/Ubuntu terminal
sudo service redis-server start
```

### 6. Run Backend
```bash
uvicorn app.main:app --reload
```

### 7. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/github` | GitHub OAuth redirect |
| GET | `/auth/github/callback` | GitHub OAuth callback |

### Chats
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chats/` | Create new chat |
| GET | `/chats/` | Get all user chats |
| GET | `/chats/{id}` | Get chat with messages |
| PATCH | `/chats/{id}` | Update chat title |
| DELETE | `/chats/{id}` | Delete chat |

### Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chats/{id}/messages` | Send message (full response) |
| POST | `/chats/{id}/messages/stream` | Send message (streaming) |
| GET | `/chats/{id}/messages` | Get all messages |

## Database Structure

### Users Collection
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "hashed_password": "string or null",
  "github_id": "string or null",
  "created_at": "datetime"
}
```

### Chats Collection
```json
{
  "_id": "ObjectId",
  "user_id": "string",
  "title": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Messages Collection
```json
{
  "_id": "ObjectId",
  "chat_id": "string",
  "role": "user | assistant",
  "content": "string",
  "created_at": "datetime"
}
```

## Redis Key Structure
| Key Pattern | Value | TTL |
|-------------|-------|-----|
| `refresh:<token>` | user_id | 30 days |
| `chat_messages:<chat_id>` | JSON array of messages | 30 minutes |