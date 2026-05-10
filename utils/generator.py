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


def _strip_markdown_code_fences(raw_text: str) -> str:
    """Strip markdown code fences (e.g. ```yaml ... ```) from text."""
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def _safe_json_loads(raw_text: str, context: str):
    """Safely parse JSON (or YAML fallback) from LLM output."""
    cleaned = _strip_markdown_code_fences(raw_text)

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

    def _post_process_dsl(self, dsl: dict, workflow_type: str) -> dict:
        """Ensure DSL structure matches working template perfectly."""
        # 1. Fix mode
        from app_config import WORKFLOW_TYPES
        if workflow_type in WORKFLOW_TYPES:
            dsl.setdefault("app", {})["mode"] = WORKFLOW_TYPES[workflow_type]["mode"]

        # 2. Fix nodes
        nodes = dsl.get("workflow", {}).get("graph", {}).get("nodes", [])
        node_id_to_type = {}

        for node in nodes:
            # Ensure type: custom
            node["type"] = "custom"
            
            # 2a. Heal node structure: Move UI fields out of data if AI nested them
            data = node.setdefault("data", {})
            if not isinstance(data, dict):
                node["data"] = {}
                data = node["data"]

            # Move layout fields from data to top level
            for field in ["width", "height", "selected", "sourcePosition", "targetPosition", "zIndex", "position", "positionAbsolute"]:
                if field in data:
                    val = data.pop(field)
                    if val is not None:
                        node[field] = val
            
            # 2b. NEVER allow null position
            if node.get("position") is None:
                node["position"] = {"x": 80, "y": 200}
            if node.get("positionAbsolute") is None:
                node["positionAbsolute"] = node["position"]

            # Default dimensions if still missing
            node.setdefault("width", 244)
            node.setdefault("height", 90)
            node.setdefault("selected", False)
            node.setdefault("sourcePosition", "right")
            node.setdefault("targetPosition", "left")
            node.setdefault("zIndex", 0)

            # Specific fixes for node types
            node_type = data.get("type", "llm") # Default to llm if type missing
            if node_type == "variable-assigner":
                node_type = "assigner"
            elif node_type == "variable-aggregator":
                node_type = "variable-aggregator"
            
            data["type"] = node_type
            data.setdefault("title", node_type.capitalize())
            node_id_to_type[node["id"]] = node_type

            # Specific fixes for if-else
            if node_type == "if-else":
                for case in data.get("cases", []):
                    for cond in case.get("conditions", []):
                        if cond.get("varType") == "boolean" and isinstance(
                            cond.get("value"), bool
                        ):
                            cond["value"] = "true" if cond["value"] else "false"

        # 3. Fix edges
        edges = dsl.get("workflow", {}).get("graph", {}).get("edges", [])
        for edge in edges:
            edge["type"] = "custom"
            edge.setdefault("zIndex", 0)
            edge.setdefault("selected", False)
            edge_data = edge.setdefault("data", {})
            edge_data.setdefault("isInIteration", False)
            edge_data.setdefault("isInLoop", False)
            
            # Ensure edge metadata matches our renamed node types
            if "source" in edge:
                edge_data["sourceType"] = node_id_to_type.get(edge["source"], edge_data.get("sourceType", "unknown"))
            if "target" in edge:
                edge_data["targetType"] = node_id_to_type.get(edge["target"], edge_data.get("targetType", "unknown"))

        # 4. Fix file upload logic
        dsl = self._fix_file_upload_logic(dsl, workflow_type)

        return dsl

    def _fix_file_upload_logic(self, dsl: dict, workflow_type: str) -> dict:
        """
        Ensure file variables in Start node have required settings.
        Also handles the global features.file_upload.enabled flag.
        """
        nodes = dsl.get("workflow", {}).get("graph", {}).get("nodes", [])
        start_node = next((n for n in nodes if n.get("data", {}).get("type") == "start"), None)
        
        has_file_var = False
        file_var_is_list = False
        if start_node:
            variables = start_node.get("data", {}).get("variables", [])
            for var in variables:
                if var.get("type") in ["file", "file-list", "files"]:
                    has_file_var = True
                    # Normalize to 'file' if it's a single file, or if it's the legacy 'files'
                    if var.get("number_limits") == 1 or var.get("type") == "files":
                        var["type"] = "file"
                    
                    if var.get("type") == "file-list":
                        file_var_is_list = True
                    else:
                        file_var_is_list = False
                    # Ensure required fields for UI button
                    var.setdefault("allowed_file_upload_methods", ["local_file"])
                    var.setdefault("allowed_file_types", ["document"])
                    var.setdefault("allowed_file_extensions", [])
                    var.setdefault("number_limits", 1)
                    var.setdefault("required", True)

        # Fix document-extractor nodes
        for node in nodes:
            data = node.get("data", {})
            if data.get("type") == "document-extractor":
                data.setdefault("is_array_file", file_var_is_list)

        # For Workflow mode, if we have per-variable upload, the global feature should be disabled
        # as it's primarily for chat-based upload.
        if workflow_type == "workflow":
            features = dsl.get("workflow", {}).get("features", {})
            if has_file_var:
                if "file_upload" not in features:
                    features["file_upload"] = {}
                features["file_upload"]["enabled"] = False
        
        return dsl

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
- If workflow_type == "chatflow", use Answer node (NOT End) and set mode: advanced-chat
- Use 'variable-aggregator' ONLY for merging outputs from multiple parallel branches.
- Use 'assigner' ONLY for writing a value into a Conversation or Environment variable.
- If merging branches, use the 'variable-aggregator' structure (variables: [list of selectors]).
- If setting a variable, use the 'assigner' structure (assigned_variable_selector, write_mode, input_variable_selector).
- Do NOT use 'variable-assigner' (legacy).
- Do NOT invent new node types.
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

            # 5. Validate and Post-process YAML
            cleaned_dsl = _strip_markdown_code_fences(raw_dsl)
            dsl = yaml.safe_load(cleaned_dsl)
            if not isinstance(dsl, dict):
                raise ValueError("AI did not return valid DSL YAML")

            dsl = self._post_process_dsl(dsl, workflow_type)
            
            generation_time = round(time.time() - start_time, 2)

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
            cleaned = _strip_markdown_code_fences(raw)
            return {"success": True, "dsl": cleaned, "error": None}
        except Exception as e:
            logger.error(f"Refinement failed: {str(e)}")
            return {"success": False, "dsl": None, "error": str(e)}