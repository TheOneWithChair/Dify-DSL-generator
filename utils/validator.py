"""DSL Validation and Analysis"""

import yaml
import re
import logging
from typing import Dict, List, Tuple

from app_config import LOGGERS

# Get logger for this module
logger = LOGGERS["dify.validator"]


class DifyDSLValidator:

    VALID_NODE_TYPES = [
        "start",
        "end",
        "answer",
        "llm",
        "knowledge-retrieval",
        "tool",
        "code",
        "if-else",
        "question-classifier",
        "parameter-extractor",
        "iteration",
        "http-request",
        "template-transform",
        "variable-assigner",
        "assigner",
        "variable-aggregator",
    ]

    VALID_WORKFLOW_MODES = ["chatflow", "workflow", "agent", "advanced-chat", "agent-chat"]

    @staticmethod
    def validate_dsl(dsl_yaml: str) -> Tuple[bool, List[str], Dict]:
        """Validate Dify DSL YAML.

        Returns:
            (is_valid, errors, stats)
        """
        logger.info("Starting DSL validation")
        logger.debug(f"DSL length: {len(dsl_yaml)} characters")

        errors = []
        stats = {
            "nodes": 0,
            "edges": 0,
            "node_types": {},
            "workflow_type": None,
            "has_start": False,
            "has_end": False,
        }

        try:
            dsl = yaml.safe_load(dsl_yaml)
            logger.debug("Successfully parsed YAML")

            # Validate top-level structure
            errors.extend(DifyDSLValidator._validate_structure(dsl, stats))

            # Validate nodes
            if "workflow" in dsl and "graph" in dsl["workflow"]:
                graph = dsl["workflow"]["graph"]

                if "nodes" in graph:
                    node_errors, node_stats = DifyDSLValidator._validate_nodes(
                        graph["nodes"], stats["workflow_type"]
                    )
                    errors.extend(node_errors)
                    stats.update(node_stats)

                # Validate edges
                if "edges" in graph and "nodes" in graph:
                    edge_errors = DifyDSLValidator._validate_edges(
                        graph["edges"], graph["nodes"]
                    )
                    errors.extend(edge_errors)
                    stats["edges"] = len(graph.get("edges", []))

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {str(e)}")
            errors.append(f"❌ YAML parsing error: {str(e)}")
            return False, errors, stats

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            errors.append(f"❌ Validation error: {str(e)}")
            return False, errors, stats

        critical_errors = len([e for e in errors if e.startswith("❌")])
        warnings = len([e for e in errors if e.startswith("⚠")])
        is_valid = critical_errors == 0

        logger.info(
            f"DSL validation completed. Valid: {is_valid}, "
            f"Critical errors: {critical_errors}, Warnings: {warnings}"
        )
        logger.info(
            f"Statistics: {stats['nodes']} nodes, {stats['edges']} edges, "
            f"Type: {stats.get('workflow_type', 'N/A')}"
        )

        return is_valid, errors, stats

    @staticmethod
    def _validate_structure(dsl: dict, stats: dict) -> List[str]:
        """Validate top-level DSL structure"""
        errors = []

        if "version" not in dsl:
            errors.append("❌ Missing 'version' field")
        elif dsl["version"] != "0.5.0":
            errors.append(
                f"⚠ Version {dsl['version']} may not be compatible (expected 0.5.0)"
            )

        if "kind" not in dsl:
            errors.append("❌ Missing 'kind' field")
        elif dsl["kind"] != "app":
            errors.append(f"❌ Invalid kind '{dsl['kind']}' (expected 'app')")

        if "app" not in dsl:
            errors.append("❌ Missing 'app' section")
            return errors

        app = dsl["app"]

        if "mode" not in app:
            errors.append("❌ Missing workflow mode (chatflow/workflow/agent/advanced-chat)")
        elif app["mode"] not in DifyDSLValidator.VALID_WORKFLOW_MODES:
            errors.append(f"❌ Invalid mode '{app['mode']}'")
        else:
            stats["workflow_type"] = app["mode"]

        if "name" not in app:
            errors.append("⚠ Missing app name")

        if "workflow" not in dsl:
            errors.append("❌ Missing 'workflow' section")
            return errors

        if "graph" not in dsl["workflow"]:
            errors.append("❌ Missing 'graph' section")
            return errors

        return errors

    @staticmethod
    def _validate_nodes(nodes: list, workflow_type: str) -> Tuple[List[str], Dict]:
        """Validate workflow nodes"""
        errors = []
        stats = {
            "nodes": len(nodes),
            "node_types": {},
            "has_start": False,
            "has_end": False,
        }

        if not nodes:
            errors.append("❌ No nodes defined")
            return errors, stats

        node_ids = set()

        for i, node in enumerate(nodes):
            if "id" not in node:
                errors.append(f"❌ Node {i} missing 'id'")
                continue

            node_id = node["id"]

            if node_id in node_ids:
                errors.append(f"❌ Duplicate node ID: {node_id}")

            node_ids.add(node_id)

            if "data" not in node:
                errors.append(f"❌ Node {node_id} missing 'data'")
                continue

            data = node["data"]

            if "type" not in data:
                errors.append(f"❌ Node {node_id} missing 'type'")
                continue

            node_type = data["type"]

            if node_type not in DifyDSLValidator.VALID_NODE_TYPES:
                errors.append(f"⚠ Unknown node type: {node_type}")

            stats["node_types"][node_type] = stats["node_types"].get(node_type, 0) + 1

            if node_type == "start":
                stats["has_start"] = True
            elif node_type in ["answer", "end"]:
                stats["has_end"] = True

            if "position" not in node:
                errors.append(f"⚠ Node {node_id} missing position")

            node_errors = DifyDSLValidator._validate_node_config(
                node_id, node_type, data
            )
            errors.extend(node_errors)

        if not stats["has_start"]:
            errors.append("❌ Workflow missing 'start' node")

        if not stats["has_end"]:
            if workflow_type in ["chatflow", "advanced-chat"]:
                errors.append("❌ Chatflow must end with 'answer' node")
            else:
                errors.append("❌ Workflow must end with 'end' node")

        if workflow_type in ["chatflow", "advanced-chat"]:
            if (
                "answer" not in stats["node_types"]
                and "end" in stats["node_types"]
            ):
                errors.append("⚠ Chatflow should end with 'answer' not 'end'")
        elif workflow_type in ["workflow", "agent", "agent-chat"]:
            if (
                "end" not in stats["node_types"]
                and "answer" in stats["node_types"]
            ):
                errors.append("⚠ Workflow should end with 'end' not 'answer'")

        return errors, stats

    @staticmethod
    def _validate_node_config(node_id: str, node_type: str, data: dict) -> List[str]:
        """Validate node-specific configuration"""
        errors = []

        if node_type == "llm":
            if "model" not in data:
                errors.append(f"❌ LLM node {node_id} missing 'model' configuration")
            if "prompt_template" not in data:
                errors.append(f"❌ LLM node {node_id} missing 'prompt_template'")

        elif node_type == "knowledge-retrieval":
            if "query_variable_selector" not in data:
                errors.append(
                    f"❌ KB node {node_id} missing 'query_variable_selector'"
                )
            if "dataset_ids" not in data:
                errors.append(f"❌ KB node {node_id} missing 'dataset_ids'")

        elif node_type == "code":
            if "code" not in data:
                errors.append(f"❌ Code node {node_id} missing 'code'")
            if "code_language" not in data:
                errors.append(f"❌ Code node {node_id} missing 'code_language'")
            if "outputs" not in data:
                errors.append(f"⚠ Code node {node_id} missing 'outputs' definition")

        elif node_type == "if-else":
            if (
                "cases" not in data
                or not isinstance(data["cases"], list)
                or len(data["cases"]) == 0
            ):
                errors.append(f"❌ If-else node {node_id} missing 'cases'")
            else:
                for case in data["cases"]:
                    if "conditions" not in case or not isinstance(
                        case["conditions"], list
                    ):
                        errors.append(
                            f"❌ If-else node {node_id} case "
                            f"'{case.get('case_id', '?')}' missing 'conditions'"
                        )

        elif node_type == "question-classifier":
            if "classes" not in data:
                errors.append(f"❌ Classifier node {node_id} missing 'classes'")
            elif len(data["classes"]) < 2:
                errors.append(
                    f"⚠ Classifier node {node_id} should have at least 2 classes"
                )

        elif node_type == "parameter-extractor":
            if "parameters" not in data:
                errors.append(
                    f"❌ Parameter extractor {node_id} missing 'parameters'"
                )

        elif node_type == "iteration":
            if "iterator_selector" not in data:
                errors.append(
                    f"❌ Iteration node {node_id} missing 'iterator_selector'"
                )

        elif node_type == "http-request":
            if "method" not in data:
                errors.append(f"❌ HTTP node {node_id} missing 'method'")
            if "url" not in data:
                errors.append(f"❌ HTTP node {node_id} missing 'url'")

        elif node_type == "start":
            if "variables" not in data:
                errors.append(f"⚠ Start node {node_id} has no input variables")

        elif node_type == "answer":
            if "answer" not in data:
                errors.append(f"❌ Answer node {node_id} missing 'answer' field")

        elif node_type == "end":
            if "outputs" not in data:
                errors.append(f"⚠ End node {node_id} has no outputs defined")

        return errors

    @staticmethod
    def _validate_edges(edges: list, nodes: list) -> List[str]:
        """Validate workflow edges"""
        errors = []

        if not edges:
            errors.append("⚠ No edges defined (nodes are disconnected)")
            return errors

        node_ids = {node["id"] for node in nodes}
        edge_ids = set()
        connected_nodes = set()

        for i, edge in enumerate(edges):
            if "id" not in edge:
                errors.append(f"⚠ Edge {i} missing 'id'")
            elif edge["id"] in edge_ids:
                errors.append(f"⚠ Duplicate edge ID: {edge['id']}")
            else:
                edge_ids.add(edge["id"])

            if "source" not in edge:
                errors.append(f"❌ Edge {i} missing 'source'")
                continue

            if "target" not in edge:
                errors.append(f"❌ Edge {i} missing 'target'")
                continue

            if edge["source"] not in node_ids:
                errors.append(
                    f"❌ Edge {i} source '{edge['source']}' not found in nodes"
                )
            if edge["target"] not in node_ids:
                errors.append(
                    f"❌ Edge {i} target '{edge['target']}' not found in nodes"
                )

            connected_nodes.add(edge["source"])
            connected_nodes.add(edge["target"])

        orphaned = node_ids - connected_nodes
        if orphaned:
            orphaned_non_start = [
                nid
                for nid in orphaned
                if not any(
                    n["id"] == nid and n["data"]["type"] == "start" for n in nodes
                )
            ]
            if orphaned_non_start:
                errors.append(f"⚠ Orphaned nodes: {', '.join(orphaned_non_start)}")

        return errors

    @staticmethod
    def analyze_complexity(dsl_yaml: str) -> Dict:
        """Analyze workflow complexity"""
        logger.info("Starting complexity analysis")
        try:
            dsl = yaml.safe_load(dsl_yaml)
            nodes = dsl.get("workflow", {}).get("graph", {}).get("nodes", [])
            edges = dsl.get("workflow", {}).get("graph", {}).get("edges", [])

            node_types = {}
            for node in nodes:
                ntype = node.get("data", {}).get("type")
                node_types[ntype] = node_types.get(ntype, 0) + 1

            complexity_score = 0
            complexity_score += len(nodes) * 2
            complexity_score += node_types.get("iteration", 0) * 10
            complexity_score += node_types.get("if-else", 0) * 5
            complexity_score += node_types.get("question-classifier", 0) * 5
            complexity_score += node_types.get("code", 0) * 3
            complexity_score += node_types.get("llm", 0) * 2

            if complexity_score < 20:
                complexity_level = "Simple"
            elif complexity_score < 50:
                complexity_level = "Moderate"
            else:
                complexity_level = "Complex"

            result = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": node_types,
                "has_loops": node_types.get("iteration", 0) > 0,
                "has_branching": (
                    node_types.get("if-else", 0) > 0
                    or node_types.get("question-classifier", 0) > 0
                ),
                "has_tools": (
                    node_types.get("tool", 0) > 0
                    or node_types.get("http-request", 0) > 0
                ),
                "has_code": node_types.get("code", 0) > 0,
                "llm_nodes": node_types.get("llm", 0),
                "complexity_score": complexity_score,
                "complexity_level": complexity_level,
            }

            logger.info(
                f"Complexity analysis completed. Level: {complexity_level}, "
                f"Score: {complexity_score}"
            )
            return result

        except Exception as e:
            logger.error(f"Complexity analysis failed: {str(e)}")
            return {
                "total_nodes": 0,
                "total_edges": 0,
                "complexity_level": "Unknown",
                "error": True,
            }

    @staticmethod
    def extract_variable_references(dsl_yaml: str) -> Dict:
        """Extract all variable references from DSL"""
        try:
            pattern = r"\{\{#([^#]+)\.([^#]+)#\}\}"
            matches = re.findall(pattern, dsl_yaml)

            references = {}
            for node_id, var_name in matches:
                if node_id not in references:
                    references[node_id] = set()
                references[node_id].add(var_name)

            return {
                "total_references": len(matches),
                "unique_nodes_referenced": len(references),
                "references_by_node": {k: list(v) for k, v in references.items()},
            }
        except Exception:
            return {"error": True}

    @staticmethod
    def get_node_statistics(dsl_yaml: str) -> Dict:
        """Get detailed node statistics"""
        try:
            dsl = yaml.safe_load(dsl_yaml)
            nodes = dsl.get("workflow", {}).get("graph", {}).get("nodes", [])

            stats = {
                "total": len(nodes),
                "by_type": {},
                "with_position": 0,
                "with_description": 0,
                "average_x_position": 0,
                "position_range": {"min_x": float("inf"), "max_x": 0},
            }

            total_x = 0
            for node in nodes:
                node_type = node.get("data", {}).get("type", "unknown")
                stats["by_type"][node_type] = stats["by_type"].get(node_type, 0) + 1

                if "position" in node:
                    stats["with_position"] += 1
                    x = node["position"].get("x", 0)
                    total_x += x
                    stats["position_range"]["min_x"] = min(
                        stats["position_range"]["min_x"], x
                    )
                    stats["position_range"]["max_x"] = max(
                        stats["position_range"]["max_x"], x
                    )

                if node.get("data", {}).get("desc"):
                    stats["with_description"] += 1

            if stats["with_position"] > 0:
                stats["average_x_position"] = total_x / stats["with_position"]

            return stats

        except Exception:
            return {"error": True}