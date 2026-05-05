"""DSL Generation Logic using Google Gemini API"""

import time
import json
import yaml
import logging
import os

import google.generativeai as genai
from config.settings import Settings
from app_config import DEFAULT_MODEL, MAX_TOKENS, LOGGERS
from prompts.system_prompts import (
    MASTER_SYSTEM_PROMPT,
    WORKFLOW_GENERATION_PROMPT,
)
from prompts.node_library import (
    NODE_SPECS,
    DSL_SPEC,
    SKILL_SPEC,
)

logger = LOGGERS["dify.generator"]


def _safe_json_loads(raw_text: str, context: str):
    """Safely parse JSON (or YAML fallback) from LLM output."""
    cleaned = raw_text.strip()

    # Strip code fences
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Try JSON first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: try YAML
    try:
        parsed = yaml.safe_load(cleaned)
        if isinstance(parsed, dict) and "workflow" in parsed:
            return parsed["workflow"]["graph"]["nodes"]
    except Exception:
        pass

    logger.error(f"{context}: Invalid JSON/YAML returned by LLM")
    logger.error(f"Raw LLM output:\n{raw_text}")
    raise ValueError(f"{context}: failed to parse LLM output")


def _generate_id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000)}"


def _normalize_if_else_conditions(dsl: dict):
    """Normalize boolean values in if-else conditions to strings."""
    nodes = dsl.get("workflow", {}).get("graph", {}).get("nodes", [])
    for node in nodes:
        data = node.get("data", {})
        if data.get("type") == "if-else":
            for case in data.get("cases", []):
                for cond in case.get("conditions", []):
                    if cond.get("varType") == "boolean" and isinstance(
                        cond.get("value"), bool
                    ):
                        cond["value"] = "true" if cond["value"] else "false"


class DifyDSLGenerator:
    def __init__(self):
        logger.info("Initializing Gemini DSL Generator")
        try:
            genai.configure(api_key=Settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(model_name=Settings.GEMINI_MODEL)
            logger.info(f"✅ Gemini initialized: {Settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {str(e)}")
            raise Exception(f"Initialization error: {str(e)}")

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Make a single call to Gemini and return the text response."""
        combined = f"{system_prompt}\n\n{user_message}"
        response = self.model.generate_content(
            combined,
            generation_config=genai.GenerationConfig(
                max_output_tokens=MAX_TOKENS,
                temperature=0.2,
            ),
        )
        return response.text

    def _extract_intent(self, **kwargs) -> dict:
        prompt = WORKFLOW_GENERATION_PROMPT.format(**kwargs)
        raw = self._call_llm(MASTER_SYSTEM_PROMPT, prompt)
        return _safe_json_loads(raw, "Intent extraction")

    def generate_dsl(
        self,
        user_request: str,
        workflow_type: str,
        complexity: str,
        model_name: str,
        tools: list,
        expected_input: str,
        expected_output: str,
        special_requirements: str,
        performance_priority: str,
    ) -> dict:
        start_time = time.time()
        try:
            # 1. Extract semantic intent
            intent = self._extract_intent(
                user_request=user_request,
                workflow_type=workflow_type,
                complexity=complexity,
                model_name=model_name,
                tools=", ".join(tools) if tools else "None",
                expected_input=expected_input or "User provided",
                expected_output=expected_output or "Derived",
                special_requirements=special_requirements or "None",
                performance_priority=performance_priority,
            )

            # 2. Build authoritative context from .md files
            node_docs_text = "\n\n".join(
                f"## NODE: {name}\n{doc}" for name, doc in NODE_SPECS.items()
            )

            # 3. Final system prompt (AI generates FULL DSL)
            final_system_prompt = f"""
{MASTER_SYSTEM_PROMPT}

## DSL FORMAT REFERENCE
{DSL_SPEC}

## SKILL CONSTRAINTS
{SKILL_SPEC}

## NODE DEFINITIONS
{node_docs_text}

## PLANNED INTENT
Workflow Intent: {intent.get("workflow_intent", "")}
Tone: {intent.get("tone", "")}
Additional Instructions: {json.dumps(intent.get("additional_instructions", []), indent=2)}

## STRICT GENERATION RULES
- You MUST generate a COMPLETE Dify DSL YAML
- Use ONLY the node types defined above
- Decide which nodes should exist and how they connect
- If workflow_type == "workflow", use End node (NOT Answer)
- If workflow_type == "chatflow", use Answer node (NOT End)
- The variable aggregation node MUST use type: variable-assigner (NOT variable-aggregator)
- Do NOT invent new node types
- Do NOT explain the DSL
- Do NOT wrap output in markdown
- Output MUST start with: version: '0.5.0'
"""

            user_message = f"""
USER DESCRIPTION: {user_request}

EXPECTED INPUT: {expected_input}

EXPECTED OUTPUT: {expected_output}

LLM SYSTEM PROMPT FOR LLM NODES: {intent.get("llm_system_prompt", "")}

LLM USER PROMPT TEMPLATE: {intent.get("llm_user_prompt_template", "")}
"""

            # 4. Single AI call — full DSL
            raw_dsl = self._call_llm(final_system_prompt, user_message)

            # 5. Validate YAML
            dsl = yaml.safe_load(raw_dsl)
            if not isinstance(dsl, dict):
                raise ValueError("AI did not return valid DSL YAML")

            generation_time = round(time.time() - start_time, 2)
            _normalize_if_else_conditions(dsl)

            return {
                "success": True,
                "dsl": yaml.safe_dump(dsl, sort_keys=False),
                "metadata": {
                    "generation_time": generation_time,
                    "tokens_used": 0,
                    "workflow_type": workflow_type,
                    "model_used": Settings.GEMINI_MODEL,
                    "complexity": complexity,
                },
            }

        except Exception as e:
            generation_time = round(time.time() - start_time, 2)
            logger.error(f"DSL generation failed: {str(e)}")
            return {
                "success": False,
                "dsl": None,
                "error": str(e),
                "metadata": {
                    "generation_time": generation_time,
                    "workflow_type": workflow_type,
                },
            }

    def refine_dsl(self, current_dsl: str, refinement_request: str) -> dict:
        """Refine an existing DSL based on user feedback."""
        refinement_prompt = f"""
Current DSL:
{current_dsl}

REFINEMENT REQUEST:
{refinement_request}

Generate updated complete DSL YAML.
Output ONLY YAML.
"""
        try:
            raw = self._call_llm(MASTER_SYSTEM_PROMPT, refinement_prompt)
            return {"success": True, "dsl": raw, "error": None}
        except Exception as e:
            logger.error(f"Refinement failed: {str(e)}")
            return {"success": False, "dsl": None, "error": str(e)}