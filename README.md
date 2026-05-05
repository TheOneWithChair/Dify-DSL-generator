# 🤖 Dify DSL Generator

A production-ready **Streamlit** application for generating [Dify](https://dify.ai) workflow DSL files using **Google Gemini AI**. Describe your workflow in plain English — get a complete, importable Dify YAML in seconds.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🧠 **AI-Powered Generation** | Uses Google Gemini to generate complete Dify workflow DSL |
| 🔀 **Multiple Workflow Types** | Supports `chatflow`, `workflow`, and `agent` modes |
| ✅ **Built-in Validation** | Automatic DSL validation with detailed error reporting |
| 🚢 **Dify Integration** | Deploy generated workflows directly to your Dify instance |
| 📊 **Complexity Analysis** | Automatic node count, branching, and loop detection |
| ✏️ **Refinement System** | Iterate and improve generated workflows via natural language |
| ⚡ **Example Library** | Pre-built examples for common use cases |
| 📜 **Generation History** | Track, reload, and download previous generations |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd Dify-DSL-generator
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Copy `.env` and fill in your keys:

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-preview-04-17   # optional

DIFY_API_KEY=                                 # optional — only for direct deploy
DIFY_API_URL=https://api.dify.ai
```

Get a free Gemini API key at 👉 [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 5. Run the application

```bash
streamlit run app.py
```

---

## 🛠 Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | — | Your Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash-preview-04-17` | Gemini model to use |
| `DIFY_API_KEY` | No | — | Dify API key (for direct deploy) |
| `DIFY_API_URL` | No | `https://api.dify.ai` | Your Dify instance URL |

---

## 📖 Usage

### 1. Generate DSL

1. Select **Workflow Type** — `chatflow`, `workflow`, or `agent`
2. Choose a **Complexity Level** — Simple, Moderate, or Complex
3. Pick an **AI Model** — Fast, Balanced, or Maximum Quality
4. Select any **Required Tools** (Google Search, RAG, HTTP, etc.)
5. Describe your workflow in the **text area**
6. Click **🚀 Generate DSL**

### 2. Validate & Preview

- Automatic validation runs after every generation
- View **node statistics**, **edge counts**, and **type distribution**
- See a **text-based flow diagram** of your workflow
- Check **complexity score** and detect loops / branching

### 3. Deploy

- **Direct deploy**: Enter your Dify API key + URL in the sidebar → click **🚢 Deploy to Dify**
- **Manual import**: Download the `.yml` file and import it in Dify Studio via *Create Application → Import DSL File*

---

## ⚡ Example Workflows

The app ships with five ready-to-load examples:

| Example | Type | Complexity |
|---|---|---|
| Customer Support Chatbot | `chatflow` | Simple |
| Research Agent | `agent` | Complex |
| Content Moderation | `workflow` | Moderate |
| Batch Data Processing | `workflow` | Complex |
| Multi-language Translation | `workflow` | Moderate |

---

## 🗂 Project Structure

```
Dify-DSL-generator/
├── app.py                    # Streamlit UI — main entry point
├── app_config.py             # Global config, logging setup, constants
├── requirements.txt
├── .env                      # API keys (not committed)
│
├── config/
│   ├── __init__.py
│   └── settings.py           # Settings class (reads from .env)
│
├── utils/
│   ├── __init__.py
│   ├── generator.py          # DifyDSLGenerator — Gemini-powered DSL generation
│   ├── validator.py          # DifyDSLValidator — YAML structure & node checks
│   ├── dify_integration.py   # DifyIntegration — REST API client for Dify
│   ├── gemini_llm.py         # Gemini client factory helper
│   └── network_diagnostics.py# Connectivity checker
│
├── prompts/
│   ├── __init__.py
│   ├── system_prompts.py     # MASTER_SYSTEM_PROMPT + WORKFLOW_GENERATION_PROMPT
│   └── node_library.py       # Loads node .md docs into NODE_SPECS dict
│
├── context/
│   ├── dsl-format.md         # Full Dify DSL format reference
│   ├── edge-and-layout.md    # Edge & layout conventions
│   └── nodes/                # Per-node documentation (llm.md, code.md, etc.)
│
└── logs/                     # Auto-created at runtime
```

---

## 🤖 AI Models Available

| Option | Model | Best For |
|---|---|---|
| Fast & Cost-Effective | `gemini-2.5-flash-preview-04-17` | Quick prototyping |
| Balanced (Recommended) | `gemini-2.5-pro-preview-05-06` | Most workflows |
| Maximum Quality | `gemini-2.5-pro-preview-05-06` | Complex, multi-branch flows |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.