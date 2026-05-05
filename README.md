#Dify DSL Generator

Production-ready Streamlit application for generating Dify workflow DSL files using Claude AI.

## Features

AI-Powered Generation: Uses Claude Sonnet 4.5 to generate complete Dify workflows

Multiple Workflow Types: Support for chatflows, workflows, and agents

** Built-in Validation: Automatic DSL validation with detailed error reporting

Direct Dify Integration**: Deploy generated workflows directly to Dify

Complexity Analysis: Automatic workflow complexity assessment

Refinement System: Iterate and improve generated workflows

Example Library: Pre-built examples for common use cases

**Generation History: Track and reload previous generations

#0 Installation

1. Clone the repositoryes

bash

git clone <repo-url>

cd ds1-gen

2. Create Virtual Environment**

bash

python -m venv venv

venv\Scripts\Activate.ps1

3. #Install dependencies**

bash

pip install -r requirements.txt
4. **Set up environment variables**

bash

cp.env.example.env

#Edit .env and add your API keys

## Configuration

▲ Token Expiry: ~4 Hours

▲ Manual refresh required during development

5. Run the application**

bash

streamlit run app.py

## Usage

### 1. Generate DSL

1. Select workflow type (chatflow/workflow/agent)

2. Choose complexity level

3. Describe your workflow in natural language

4. Click "Generate DSL"

### 2. Validate

Automatic validation after generation

View node statistics and complexity analysis
Check for errors and warnings

### 3. Deploy

Direct deployment to Dify (if configured)

Or download YAML for manual import

## Examples

The application includes pre-built examples:

Customer Support Chatbot

Research Agent

Content Moderation

Batch Data Processing

Multi-language Translation

## Architecture

DSL-GEN

langchain_wrapper/

config/

settings.py

11m_embeddings/

11m_wrappers/

stork_provider.py

utils/

ai_token.txt

# LLM abstraction layer

##ProviderConfig #StorkConfig

##EmbeddingModels #Vectorization

# #DBSStork #ClaudeSonnet #LLMAdapter

##LLMUtilities

##SSOAuth #BearerToken #StorkAuth

utils/

generator.py

validator.py

##DSLGeneration #LLMInvoker

stork_1lm.py

network_diagnostics.py

dify_integration.py

prompts/

logs/

app.py

config.py

requirements.txt

README.md

## License

MIT License