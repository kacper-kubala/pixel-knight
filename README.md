# Pixel Knight

A cyberpunk-styled AI chat interface with support for multiple AI providers, web search, RAG, and advanced features.

## Features

### Core Features
- 🔌 **Multi-Provider Support** - Use OpenAI, Anthropic, Groq, xAI (Grok), Ollama, and more simultaneously
- 🤖 **Multiple AI Models** - Switch between models from different providers
- 🔍 **Web Search Integration** - Brave Search, DuckDuckGo, SearXNG
- 📚 **RAG Support** - Index local documents for context-aware responses
- 💾 **Session Management** - Save and organize your conversations
- 🎨 **Cyberpunk UI** - Beautiful terminal-inspired dark theme
- ⚡ **Streaming Responses** - Real-time message streaming

### Advanced Features
- 🔬 **Deep Research Agent** - Multi-round research with synthesis
- 📺 **YouTube Summarization** - Summarize videos automatically
- 🎨 **Image Generation** - DALL-E integration for creating images
- 🎤 **Voice Input** - Speech-to-text using Web Speech API
- ⚖️ **Model Comparison** - Compare responses from different models side-by-side
- 📝 **Presets** - 10+ built-in system prompt presets for different use cases
- ✨ **Markdown Rendering** - Beautiful code highlighting with highlight.js

### UX Features
- ⌨️ **Keyboard Shortcuts** - Ctrl+Enter, Ctrl+N, Escape, and more
- 📥 **Export Conversations** - Export as Markdown or JSON
- ✏️ **Edit Messages** - Edit your messages inline
- 🔎 **Search History** - Search across all your conversations
- 🔄 **Regenerate Responses** - Regenerate any AI response

### Infrastructure
- 🐳 **Docker Support** - Ready-to-use Dockerfile and docker-compose
- 🐘 **PostgreSQL Support** - Optional database backend (SQLite fallback)
- 🧪 **Tests** - pytest test suite with coverage
- 🚀 **CI/CD** - GitHub Actions workflow

## Quick Start

### One-Command Startup

```bash
./start.sh
```

That's it! The script will:
1. Create a virtual environment (if needed)
2. Install all dependencies (if needed)
3. Start the server

Then open **http://localhost:8080** in your browser.

### Manual Installation

If you prefer to run manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python run.py
```

### Docker Deployment

```bash
# Run with Docker Compose (includes PostgreSQL)
docker-compose up -d

# Run with Ollama support
docker-compose --profile with-ollama up -d

# Just build and run the app
docker build -t pixel-knight .
docker run -p 8080:8080 pixel-knight
```

---

## 🔌 Adding AI Providers

Pixel Knight supports **multiple AI providers simultaneously**. Add providers in the UI through **Settings → API Providers**.

### Supported Providers

| Provider | Models | Free Tier | API Key Required |
|----------|--------|-----------|------------------|
| 🦙 **Ollama** | Llama, Mistral, Qwen, Phi, etc. | ✅ Local | ❌ |
| 🤖 **OpenAI** | GPT-4o, GPT-4, GPT-3.5-turbo | ❌ | ✅ |
| 🧠 **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus/Haiku | ❌ | ✅ |
| ⚡ **Groq** | Llama 3, Mixtral (ultra-fast) | ✅ | ✅ |
| 𝕏 **xAI** | Grok-2, Grok-beta | ❌ | ✅ |
| 🤝 **Together AI** | 100+ open models | ✅ $25 credit | ✅ |
| 🌀 **Mistral AI** | Mistral Large, Medium, Small | ✅ | ✅ |
| 🛤️ **OpenRouter** | 200+ models, one API | Pay per use | ✅ |

### Adding a Provider (UI)

1. Click **⚙️ Settings** in the right sidebar
2. In the **API Providers** modal, click on a provider button (e.g., OpenAI, Groq)
3. Enter your API key when prompted
4. Click **Test** to verify connection
5. Models from that provider will now appear in the sidebar!

### Provider Details

#### 🦙 Ollama (Local - Recommended for Starting)

[Ollama](https://ollama.ai/) runs models locally on your machine.

```bash
# Install Ollama
brew install ollama        # macOS
curl -fsSL https://ollama.ai/install.sh | sh   # Linux

# Download models
ollama pull llama3.2
ollama pull mistral
ollama pull codellama
ollama pull qwen2.5

# Start server
ollama serve
```

**Configuration:**
- API Base: `http://localhost:11434/v1`
- No API key needed
- Pixel Knight adds Ollama by default!

#### 🤖 OpenAI

Get your API key from: https://platform.openai.com/api-keys

**Models:** `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-3.5-turbo`, `o1-preview`, `o1-mini`

#### 🧠 Anthropic (Claude)

Get your API key from: https://console.anthropic.com/

**Models:** `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`

#### ⚡ Groq (Ultra-Fast)

Get your API key from: https://console.groq.com/ (free tier available!)

**Models:** `llama-3.2-90b-vision-preview`, `llama-3.1-70b-versatile`, `mixtral-8x7b-32768`

#### 𝕏 xAI (Grok)

Get your API key from: https://console.x.ai/

**Models:** `grok-2`, `grok-beta`

#### 🤝 Together AI

Get your API key from: https://api.together.xyz/ ($25 free credit)

**Models:** 100+ open-source models including Llama, Mixtral, Qwen, CodeLlama, etc.

#### 🌀 Mistral AI

Get your API key from: https://console.mistral.ai/

**Models:** `mistral-large-latest`, `mistral-medium-latest`, `mistral-small-latest`, `open-mixtral-8x22b`

#### 🛤️ OpenRouter

Get your API key from: https://openrouter.ai/keys

**Access 200+ models** from OpenAI, Anthropic, Google, Meta, and more with a single API key!

### Adding a Custom Provider

For any OpenAI-compatible API:

1. Click **⚙️ Settings**
2. Click **Custom** button
3. Enter:
   - **Name:** Display name (e.g., "My vLLM Server")
   - **API Base URL:** Your API endpoint (e.g., `http://localhost:8000/v1`)
   - **API Key:** If required

### Managing Providers

In the API Providers modal:
- **Test** - Verify connection and fetch available models
- **ON/OFF** - Enable or disable a provider (disabled providers don't show models)
- **Edit** - Change API key or URL
- **Delete** - Remove a provider

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Default LLM API (fallback)
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=sk-no-key-required

# Search Providers
BRAVE_API_KEY=your-brave-api-key
SEARXNG_URL=http://localhost:8888

# Image Generation (DALL-E)
OPENAI_DALLE_KEY=sk-your-openai-key

# Database (optional - defaults to SQLite)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# Server
HOST=0.0.0.0
PORT=8080
```

> **Note:** Provider API keys can also be added through the UI (Settings → API Providers), which stores them locally.

---

## ☁️ Cloud Database (Supabase)

By default, Pixel Knight stores data in local JSON files. To sync data across multiple devices, use a cloud database like **Supabase** (free tier available).

### Step 1: Create Supabase Account

1. Go to **https://supabase.com** → Sign up with GitHub
2. Click **New Project**
3. Set:
   - **Name:** `pixel-knight`
   - **Database Password:** generate a strong password (save it!)
   - **Region:** choose closest to you
4. Click **Create new project** (wait ~2 minutes)

### Step 2: Get Connection String

1. In your project → **Settings** (gear icon) → **Database**
2. Scroll to **Connection string** → **URI** tab
3. Copy the connection string

### Step 3: Configure Pixel Knight

Create `.env` file:

```env
# Supabase Database (replace with your values)
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-ID]:[PASSWORD]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres

# LLM API
OPENAI_API_BASE=http://localhost:11434/v1
OPENAI_API_KEY=sk-no-key-required
```

**Important:** Change `postgresql://` to `postgresql+asyncpg://` in the URL!

### Step 4: Use on Multiple Devices

Copy the same `.env` file to each device:

```bash
# Device 1
./start.sh
# Console shows: "Using PostgreSQL database for sessions"

# Device 2 (same .env file)
./start.sh
# Same database, synced data! 🎉
```

### Alternative Cloud Databases

| Provider | Free Tier | Link |
|----------|-----------|------|
| **Supabase** | 500 MB | https://supabase.com |
| **Neon** | 512 MB | https://neon.tech |
| **Railway** | $5 credit | https://railway.app |
| **Render** | 256 MB | https://render.com |

All use the same connection string format - just update `DATABASE_URL` in `.env`.

---

## Usage

### Creating a Session

1. Click **+** or **+ Chat** next to a model
2. Enter a session name (or leave blank for auto-naming)
3. Optionally adjust **temperature**, **max tokens**, and **system prompt**
4. Start chatting!

### LLM Parameters

Click **⚙ Parameters** to adjust:
- **Temperature** (0-2): Higher = more creative, Lower = more focused
- **Max Tokens**: Maximum response length
- **System Prompt**: Instructions for the AI

### Web Search

1. Click **🔍 Search Settings** → choose provider
2. Click **Research** button to enable search for next message
3. Your query will be enriched with web results

### Deep Research

1. Click **Deep** button
2. Enter your research query
3. Set number of iterations (1-10)
4. The agent will perform multiple search rounds and synthesize findings

### RAG (Document Context)

1. Toggle **RAG** switch in right sidebar
2. Either:
   - Enter directory path → **Add**
   - Click **📁 Upload Files** to upload documents
3. Supported formats: `.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.pdf`
4. Your questions will use indexed documents as context

### YouTube Summarization

1. Click **YT** button
2. Paste YouTube video URL
3. Click **Summarize**

### Image Generation

1. Click **🎨** button (requires `OPENAI_DALLE_KEY` in .env)
2. Enter your image prompt
3. Choose size, quality, and style
4. Click **Generate**

### Voice Input

1. Click **🎤** button
2. Allow microphone access
3. Speak your message
4. Text appears in the input field

### Model Comparison

1. Click **⚖️ Compare Models** in sidebar
2. Select two models
3. Enter a prompt
4. Click **Compare** to see side-by-side responses

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Send message |
| `Ctrl+N` | New session |
| `Ctrl+K` | Focus input |
| `Ctrl+B` | Toggle sidebar |
| `Escape` | Close modal |
| `1-9` | Switch to session # |
| `?` | Show all shortcuts |

### Export & Edit

- **Export MD/JSON**: Click buttons in chat header
- **Edit Message**: Hover over your message → click ✏️
- **Regenerate**: Hover over AI response → click 🔄
- **Copy**: Hover over any message → click 📋

---

## Project Structure

```
pixel_knight/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── models.py            # Data models
│   ├── database.py          # SQLAlchemy/PostgreSQL
│   └── services/
│       ├── llm_service.py       # LLM integration
│       ├── provider_service.py  # Multi-provider management
│       ├── search_service.py    # Web search
│       ├── rag_service.py       # Document indexing
│       ├── session_service.py   # Session management
│       ├── youtube_service.py   # YouTube processing
│       ├── research_service.py  # Deep research agent
│       ├── preset_service.py    # System prompts presets
│       └── image_service.py     # DALL-E integration
├── frontend/
│   ├── index.html           # UI
│   ├── styles.css           # Cyberpunk theme
│   └── app.js               # Frontend logic
├── tests/                   # pytest tests
│   ├── conftest.py
│   ├── test_api.py
│   └── test_services.py
├── .github/workflows/       # CI/CD
│   └── ci.yml
├── data/                    # Stored sessions, indexes, providers
├── Dockerfile               # Docker build
├── docker-compose.yml       # Docker stack
├── start.sh                 # One-click startup
├── run.py                   # Python entry point
├── pytest.ini               # Test config
└── requirements.txt
```

## API Endpoints

### Providers
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/providers` | GET/POST | List or add providers |
| `/api/providers/presets` | GET | Available preset providers |
| `/api/providers/preset/{key}` | POST | Add preset provider |
| `/api/providers/{id}` | PUT/DELETE | Update or delete provider |
| `/api/providers/{id}/toggle` | POST | Enable/disable provider |
| `/api/providers/{id}/test` | POST | Test provider connection |

### Sessions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET/POST | List or create sessions |
| `/api/sessions/search` | GET | Search sessions by content |
| `/api/sessions/{id}` | GET/PUT/DELETE | Manage specific session |
| `/api/sessions/{id}/auto-name` | POST | Auto-generate session name |
| `/api/sessions/{id}/export` | GET | Export session (MD/JSON) |
| `/api/sessions/{id}/messages/{id}` | PUT | Edit a message |

### Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Send message (blocking) |
| `/api/chat/stream` | POST | Send message (streaming) |
| `/api/chat/{id}/regenerate` | POST | Regenerate response |
| `/api/compare/chat` | POST | Compare model responses |

### Features
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | List all models from enabled providers |
| `/api/rag/files` | GET | List indexed files |
| `/api/rag/index` | POST | Index directory |
| `/api/rag/upload` | POST | Upload file for RAG |
| `/api/youtube/summarize` | POST | Summarize YouTube video |
| `/api/research` | POST | Deep research agent |
| `/api/images/generate` | POST | Generate image (DALL-E) |
| `/api/images/status` | GET | Check image generation status |

### Configuration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/presets` | GET/POST | Manage system prompts |
| `/api/usage` | GET | Usage statistics |
| `/api/config` | GET/PUT | Configuration |

## Troubleshooting

### "No models available"
- Make sure at least one provider is enabled
- Click **Settings** → test your providers
- For Ollama: make sure `ollama serve` is running

### Provider test fails
- Check if the API key is correct
- Verify the API endpoint is reachable
- Some providers may have rate limits

### Models not loading
- Click **Test** on the provider to refresh model list
- Check for firewall/network issues
- Verify the API is accessible: `curl http://localhost:11434/v1/models`

### Slow responses
- Try a smaller model (e.g., `phi3` instead of `llama3.2`)
- Use Groq for faster inference
- Reduce `max_tokens` parameter
- Use GPU acceleration if available

## License

MIT License
