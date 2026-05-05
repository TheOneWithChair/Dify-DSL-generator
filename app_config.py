"""Configuration for Dify DSL Generator"""

import os
import logging
import sys
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


# Configure logging
def setup_logging():
    """Setup comprehensive logging for the application"""

    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                f"{logs_dir}/dify_generator_{datetime.now().strftime('%Y%m%d')}.log"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Create specific loggers for different components
    loggers = {
        "dify.generator": logging.getLogger("dify.generator"),
        "dify.validator": logging.getLogger("dify.validator"),
        "dify.integration": logging.getLogger("dify.integration"),
        "dify.app": logging.getLogger("dify.app"),
    }

    # Set log levels for different components
    loggers["dify.generator"].setLevel(logging.INFO)
    loggers["dify.validator"].setLevel(logging.INFO)
    loggers["dify.integration"].setLevel(logging.INFO)
    loggers["dify.app"].setLevel(logging.INFO)

    # Add file handlers for each component
    for name, logger in loggers.items():
        component_name = name.split(".")[-1]
        file_handler = logging.FileHandler(
            f"{logs_dir}/{component_name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    logging.info("Logging system initialized")
    return loggers


# Initialize logging
LOGGERS = setup_logging()

# API Keys
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_API_URL = os.getenv("DIFY_API_URL", "https://api.dify.ai")

# Gemini Model Config
DEFAULT_MODEL = "gemini-2.5-flash-preview-04-17"
MAX_TOKENS = 8000

LOGGERS["dify.app"].info(
    f"Using Gemini API with default model: {DEFAULT_MODEL}"
)

# Workflow Templates
WORKFLOW_TYPES = {
    "chatflow": {
        "name": "Chatflow",
        "icon": "💬",
        "description": "Multi-turn conversational applications (chatbots, assistants)",
        "use_cases": [
            "Customer support chatbot",
            "FAQ assistant",
            "Interactive advisor",
            "Personal assistant",
        ],
    },
    "workflow": {
        "name": "Workflow",
        "icon": "⚙️",
        "description": "Single-turn batch processing tasks (automation, data processing)",
        "use_cases": [
            "Content generation",
            "Data analysis",
            "Batch processing",
            "Report generation",
        ],
    },
    "agent": {
        "name": "Agent",
        "icon": "🤖",
        "description": "Autonomous reasoning with tool calling (research, complex tasks)",
        "use_cases": [
            "Research agent",
            "Task automation",
            "Multi-step problem solving",
            "Data gathering and analysis",
        ],
    },
}

COMPLEXITY_LEVELS = {
    "simple": {
        "name": "Simple",
        "description": "3-5 nodes, basic logic",
        "estimated_time": "Fast (<1 min)",
    },
    "moderate": {
        "name": "Moderate",
        "description": "6-10 nodes, conditional logic",
        "estimated_time": "Medium (1-2 min)",
    },
    "complex": {
        "name": "Complex",
        "description": "11+ nodes, iterations, multiple branches",
        "estimated_time": "Slower (2-5 min)",
    },
}

# Available integrations/tools
AVAILABLE_TOOLS = [
    "Google Search",
    "Knowledge Base (RAG)",
    "HTTP API Calls",
    "Code Execution (Python/JS)",
    "Database Queries",
    "Email/Slack Notifications",
    "File Processing",
    "Web Scraping",
]

# Model options for different use cases
MODEL_OPTIONS = {
    "Fast & Cost-Effective": "gemini-2.5-flash-preview-04-17",
    "Balanced (Recommended)": "gemini-2.5-pro-preview-05-06",
    "Maximum Quality": "gemini-2.5-pro-preview-05-06",
}