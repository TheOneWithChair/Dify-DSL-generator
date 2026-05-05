"""Dify DSL Generator — Streamlit Application (Gemini API Version)"""

import streamlit as st
import yaml
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# DSL GEN IMPORTS
from utils.generator import DifyDSLGenerator
from utils.validator import DifyDSLValidator
from utils.dify_integration import DifyIntegration

from app_config import (
    DIFY_API_KEY,
    DIFY_API_URL,
    WORKFLOW_TYPES,
    COMPLEXITY_LEVELS,
    AVAILABLE_TOOLS,
    MODEL_OPTIONS,
    LOGGERS,
)

from dotenv import load_dotenv

load_dotenv()

# LOGGER
logger = LOGGERS["dify.app"]

# PAGE CONFIG
st.set_page_config(
    page_title="Dify DSL Generator (Gemini)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1a7764;
    margin-bottom: 0.5rem;
}
.sub-header {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
}
.success-box {
    padding: 1rem;
    background-color: #d4edda;
    border-left: 4px solid #28a745;
    border-radius: 4px;
    margin: 1rem 0;
}
.error-box {
    padding: 1rem;
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
    border-radius: 4px;
    margin: 1rem 0;
}
.info-box {
    padding: 1rem;
    background-color: #d1ecf1;
    border-left: 4px solid #0c5460;
    border-radius: 4px;
    margin: 1rem 0;
}
.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid #dee2e6;
}
.stButton button {
    width: 100%;
}
</style>
""",
    unsafe_allow_html=True,
)

# SESSION STATE
DEFAULT_STATE = {
    "generated_dsl": None,
    "generation_metadata": None,
    "validation_results": None,
    "history": [],
    "show_refinement": False,
    "default_type": list(WORKFLOW_TYPES.keys())[0],
    "default_complexity": list(COMPLEXITY_LEVELS.keys())[0],
    "default_tools": [],
    "default_request": "",
    "default_input": "",
    "default_output": "",
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# MAIN APP
def main():
    """Main application"""
    logger.info("Starting Dify DSL Generator (Gemini)")

    # Header
    st.markdown(
        '<div class="main-header">🤖 Dify DSL Generator</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sub-header">Generate production-ready Dify workflows using natural language</div>',
        unsafe_allow_html=True,
    )

    # SIDEBAR
    with st.sidebar:
        st.header("⚙️ Configuration")

        dify_key = st.text_input(
            "Dify API Key (Optional)", value=DIFY_API_KEY, type="password"
        )
        dify_url = st.text_input("Dify API URL", value=DIFY_API_URL)

        # Gemini connection test
        if st.button("🔌 Test Gemini Connection"):
            logger.info("Testing Gemini connection")
            with st.spinner("Connecting to Gemini..."):
                try:
                    DifyDSLGenerator()
                    st.success("✅ Gemini Connected")
                except Exception as e:
                    logger.error("Gemini connection failed", exc_info=True)
                    st.error(str(e))

        st.divider()
        st.caption("Logs: dify.app")

        # Quick examples
        st.header("⚡ Quick Examples")
        example = st.selectbox(
            "Load example",
            [
                "Custom...",
                "Customer Support Chatbot",
                "Research Agent",
                "Content Moderation",
                "Batch Data Processing",
                "Multi-language Translation",
            ],
        )

        if example != "Custom...":
            st.session_state.example_loaded = example

    # MAIN TABS
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🚀 Generate DSL", "✅ Validate & Preview", "🚢 Deploy to Dify", "📜 History"]
    )

    # TAB 1 — GENERATE DSL
    with tab1:
        st.header("Generate Workflow DSL using Gemini")

        # Load example if selected
        if (
            "example_loaded" in st.session_state
            and st.session_state.example_loaded != "Custom..."
        ):
            example_configs = {
                "Customer Support Chatbot": {
                    "request": (
                        "Create a customer support chatbot that searches our knowledge base "
                        "and provides helpful answers with source citations. Include conversation memory."
                    ),
                    "type": "chatflow",
                    "complexity": "simple",
                    "tools": ["Knowledge Base (RAG)"],
                    "input": "Customer questions",
                    "output": "Helpful answers with citations",
                },
                "Research Agent": {
                    "request": (
                        "Build an autonomous research agent that searches the web, analyzes results, "
                        "and creates comprehensive research reports with citations."
                    ),
                    "type": "agent",
                    "complexity": "complex",
                    "tools": ["Google Search", "Code Execution (Python/JS)"],
                    "input": "Research topic",
                    "output": "Comprehensive research report",
                },
                "Content Moderation": {
                    "request": (
                        "Create a content moderation workflow that analyzes user-submitted content, "
                        "approves or rejects it, and provides feedback to authors."
                    ),
                    "type": "workflow",
                    "complexity": "moderate",
                    "tools": ["Code Execution (Python/JS)"],
                    "input": "User content and author ID",
                    "output": "Approval status and feedback",
                },
                "Batch Data Processing": {
                    "request": (
                        "Process 100+ customer reviews in parallel, extract sentiment and topics, "
                        "then create an aggregate summary report."
                    ),
                    "type": "workflow",
                    "complexity": "complex",
                    "tools": ["Code Execution (Python/JS)"],
                    "input": "Array of customer reviews",
                    "output": "Sentiment analysis and topic summary",
                },
                "Multi-language Translation": {
                    "request": (
                        "Translate documents into multiple languages while preserving formatting "
                        "and maintaining translation quality through validation."
                    ),
                    "type": "workflow",
                    "complexity": "moderate",
                    "tools": ["Code Execution (Python/JS)"],
                    "input": "Source document and target languages",
                    "output": "Translated documents",
                },
            }

            config = example_configs[st.session_state.example_loaded]
            default_request = config["request"]
            default_type = config["type"]
            default_complexity = config["complexity"]
            default_tools = config["tools"]
            default_input = config["input"]
            default_output = config["output"]
            del st.session_state.example_loaded
        else:
            default_request = ""
            default_type = "chatflow"
            default_complexity = "moderate"
            default_tools = []
            default_input = ""
            default_output = ""

        # User input form
        with st.form("generation_form"):
            st.subheader("Workflow Requirements")
            col1, col2 = st.columns(2)

            with col1:
                workflow_type = st.selectbox(
                    "Workflow Type",
                    options=list(WORKFLOW_TYPES.keys()),
                    format_func=lambda k: WORKFLOW_TYPES[k]["name"],
                    index=list(WORKFLOW_TYPES.keys()).index(
                        st.session_state["default_type"]
                    ),
                    help="Select the type of workflow you want to create",
                )
                st.caption(WORKFLOW_TYPES[workflow_type]["description"])

                complexity = st.selectbox(
                    "Complexity Level",
                    options=list(COMPLEXITY_LEVELS.keys()),
                    format_func=lambda k: COMPLEXITY_LEVELS[k]["name"],
                    index=list(COMPLEXITY_LEVELS.keys()).index(
                        st.session_state["default_complexity"]
                    ),
                    help="Higher complexity = more nodes and features",
                )
                st.caption(f"⏱ {COMPLEXITY_LEVELS[complexity]['estimated_time']}")

            with col2:
                model_selection = st.selectbox(
                    "AI Model",
                    options=list(MODEL_OPTIONS.keys()),
                    index=1,
                    help="Choose based on speed vs quality trade-off",
                )
                selected_tools = st.multiselect(
                    "Required Tools",
                    options=AVAILABLE_TOOLS,
                    default=st.session_state["default_tools"],
                    help="Select tools your workflow needs",
                )

            user_request = st.text_area(
                "Describe Workflow",
                value=st.session_state["default_request"],
                height=150,
                placeholder=(
                    "Example: Create a customer support chatbot that searches "
                    "our knowledge base and provides helpful answers..."
                ),
                help="Describe what you want your workflow to do",
            )

            expected_input = st.text_input(
                "Expected Input",
                value=st.session_state["default_input"],
                placeholder="e.g., Customer questions, Documents to process",
                help="What data will users provide?",
            )

            expected_output = st.text_input(
                "Desired Output",
                value=st.session_state["default_output"],
                placeholder="e.g., Helpful answers, Processed data",
                help="What should the workflow produce?",
            )

            special_requirements = st.text_area(
                "Special Requirements (Optional)",
                placeholder="Any specific requirements? e.g., Must handle images, Need rate limiting, etc.",
                height=80,
            )

            col5, col6 = st.columns([3, 1])
            with col5:
                performance_priority = st.radio(
                    "Performance Priority",
                    options=[
                        "Speed (faster, lower quality)",
                        "Balanced",
                        "Quality (slower, higher quality)",
                    ],
                    index=1,
                    horizontal=True,
                )
            with col6:
                st.write("")  # Spacer
                generate_button = st.form_submit_button(
                    "🚀 Generate DSL",
                    type="primary",
                    use_container_width=True,
                )

        # GENERATE ACTION
        if generate_button:
            if not user_request:
                st.error("❌ Please describe your workflow")
                return

            logger.info(
                f"Starting DSL generation - Type: {workflow_type}, complexity: {complexity}"
            )
            logger.info(
                f"User request: {user_request[:100]}{'...' if len(user_request) > 100 else ''}"
            )

            start_time = datetime.now()

            with st.spinner("Generating DSL via Gemini..."):
                generator = DifyDSLGenerator()

                perf_map = {
                    "Speed (faster, lower quality)": "speed",
                    "Balanced": "balanced",
                    "Quality (slower, higher quality)": "quality",
                }

                result = generator.generate_dsl(
                    user_request=user_request,
                    workflow_type=workflow_type,
                    complexity=complexity,
                    model_name=MODEL_OPTIONS[model_selection],
                    tools=selected_tools,
                    expected_input=expected_input,
                    expected_output=expected_output,
                    special_requirements=special_requirements,
                    performance_priority=perf_map[performance_priority],
                )

            if result["success"]:
                logger.info("DSL generation successful")
                duration = (datetime.now() - start_time).total_seconds()
                st.session_state.generated_dsl = result["dsl"]
                st.session_state.generation_metadata = {
                    "generation_time": round(duration, 2),
                    "model_used": MODEL_OPTIONS[model_selection],
                }

                st.session_state.history.append(
                    {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "request": user_request,
                        "workflow_type": workflow_type,
                        "complexity": complexity,
                        "dsl": result["dsl"],
                        "metadata": st.session_state.generation_metadata,
                    }
                )

                st.success("✅ DSL Generated")
                logger.info(
                    f"DSL added to history. Total history items: {len(st.session_state.history)}"
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Generation Time",
                        f"{result['metadata']['generation_time']}s",
                    )
                with col2:
                    st.metric("Tokens Used", result["metadata"]["tokens_used"])
                with col3:
                    st.metric(
                        "Model",
                        result["metadata"]["model_used"].split("-")[1].title(),
                    )

                # Auto-validate
                logger.info("Auto-validating generated DSL")
                validator = DifyDSLValidator()
                is_valid, errors, stats = validator.validate_dsl(result["dsl"])
                st.session_state.validation_results = (is_valid, errors, stats)

                if is_valid:
                    st.success(
                        f"✅ DSL is valid! Contains {stats['nodes']} nodes and {stats['edges']} edges"
                    )
                    logger.info(
                        f"Auto-validation successful. {stats['nodes']} nodes, {stats['edges']} edges"
                    )
                else:
                    st.warning(
                        "⚠ DSL generated but has validation issues. Check the Validate tab."
                    )
                    logger.warning(
                        f"Auto-validation found issues. "
                        f"{len([e for e in errors if e.startswith('❌')])} critical errors"
                    )
            else:
                logger.error("DSL generation failed")
                st.error(result["error"])

        # SHOW GENERATED DSL
        if st.session_state.generated_dsl:
            st.divider()
            st.subheader("Generated DSL")

            col1, col2, col3 = st.columns([1, 1, 1])

            with col1:
                if st.button("📋 Copy to clipboard"):
                    st.code(st.session_state.generated_dsl, language="yaml")
                    st.info("ℹ Use Ctrl+A then Ctrl+C to copy")

            with col2:
                st.download_button(
                    "⬇️ Download YAML",
                    data=st.session_state.generated_dsl,
                    file_name=f"dify_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml",
                    mime="text/yaml",
                )

            with col3:
                if st.button("✏️ Refine DSL"):
                    st.session_state.show_refinement = True

            if st.session_state.show_refinement:
                with st.form("refinement_form"):
                    refine_text = st.text_area("Describe refinement", height=100)
                    apply = st.form_submit_button("✅ Apply Refinement")

                    if apply and refine_text:
                        generator = DifyDSLGenerator()
                        result = generator.refine_dsl(
                            st.session_state.generated_dsl, refine_text
                        )
                        if result["success"]:
                            st.session_state.generated_dsl = result["dsl"]
                            st.session_state.show_refinement = False
                            st.success("✅ Refinement applied")
                            st.rerun()
                        else:
                            st.error(result["error"])

            st.code(st.session_state.generated_dsl, language="yaml", line_numbers=True)

    # TAB 2 — VALIDATE
    with tab2:
        st.header("Validate & Preview DSL")

        if not st.session_state.generated_dsl:
            st.info("ℹ Generate a DSL first or paste one below")

            uploaded_file = st.file_uploader(
                "Upload existing DSL", type=["yml", "yaml"]
            )
            if uploaded_file:
                st.session_state.generated_dsl = uploaded_file.read().decode("utf-8")
                st.rerun()

            pasted_dsl = st.text_area(
                "Or paste DSL here",
                height=300,
                placeholder="Paste your Dify DSL YAML here...",
            )

            if st.button("Validate Pasted DSL") and pasted_dsl:
                st.session_state.generated_dsl = pasted_dsl
                st.rerun()

        else:
            # Validation
            validator = DifyDSLValidator()

            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("Validation Results")
            with col2:
                if st.button("🔄 Re-validate"):
                    is_valid, errors, stats = validator.validate_dsl(
                        st.session_state.generated_dsl
                    )
                    st.session_state.validation_results = (is_valid, errors, stats)

            # Run validation if not done
            if not st.session_state.validation_results:
                is_valid, errors, stats = validator.validate_dsl(
                    st.session_state.generated_dsl
                )
                st.session_state.validation_results = (is_valid, errors, stats)

            is_valid, errors, stats = st.session_state.validation_results

            # Show validation status
            if is_valid:
                st.success("✅ DSL is valid and ready to import!")

            critical_errors = [e for e in errors if e.startswith("❌")]
            warnings = [e for e in errors if e.startswith("⚠")]

            if critical_errors:
                st.error(f"❌ Found {len(critical_errors)} critical error(s)")
            if warnings:
                st.warning(f"⚠ Found {len(warnings)} warning(s)")

            # Show errors/warnings
            if errors:
                with st.expander("🔍 Validation Details", expanded=not is_valid):
                    for error in errors:
                        if error.startswith("❌"):
                            st.error(error)
                        elif error.startswith("⚠"):
                            st.warning(error)
                        else:
                            st.info(error)

            # Workflow statistics
            st.subheader("Workflow Statistics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Nodes", stats.get("nodes", 0))
            with col2:
                st.metric("Total Edges", stats.get("edges", 0))
            with col3:
                workflow_type_stat = stats.get("workflow_type") if stats else None
                st.metric("Workflow Type", (workflow_type_stat or "N/A").title())
            with col4:
                has_start = "✅" if stats.get("has_start") else "❌"
                has_end = "✅" if stats.get("has_end") else "❌"
                st.metric("Start/End Nodes", f"{has_start} / {has_end}")

            # Node type breakdown
            if stats.get("node_types"):
                st.subheader("Node Type Distribution")
                node_types = stats["node_types"]

                cols = st.columns(min(4, len(node_types)))
                for i, (node_type, count) in enumerate(node_types.items()):
                    with cols[i % len(cols)]:
                        st.metric(node_type.replace("-", " ").title(), count)

            # Complexity analysis
            complexity_analysis = validator.analyze_complexity(
                st.session_state.generated_dsl
            )

            if complexity_analysis:
                st.subheader("Complexity Analysis")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Complexity Level",
                        complexity_analysis.get("complexity_level", "Unknown"),
                        help="Based on node count and types",
                    )
                with col2:
                    loop_status = (
                        "Yes" if complexity_analysis.get("has_loops") else "No"
                    )
                    st.metric("Has Loops", loop_status)
                with col3:
                    branch_status = (
                        "Yes" if complexity_analysis.get("has_branching") else "No"
                    )
                    st.metric("Has Branching", branch_status)

            # Visual preview (simplified)
            st.subheader("Workflow Preview")
            try:
                dsl_data = yaml.safe_load(st.session_state.generated_dsl)
                nodes = (
                    dsl_data.get("workflow", {}).get("graph", {}).get("nodes", [])
                )
                edges = (
                    dsl_data.get("workflow", {}).get("graph", {}).get("edges", [])
                )

                st.text("Workflow Flow:")
                node_dict = {
                    node["id"]: node["data"].get("title", node["id"])
                    for node in nodes
                }
                flow_lines = []
                for edge in edges[:10]:  # Limit to first 10 edges
                    source = node_dict.get(edge["source"], edge["source"])
                    target = node_dict.get(edge["target"], edge["target"])
                    flow_lines.append(f"{source} → {target}")

                for line in flow_lines:
                    st.text(f"  {line}")

                if len(edges) > 10:
                    st.text(f"  ... and {len(edges) - 10} more connections")

            except Exception as e:
                st.error(f"Could not generate preview: {str(e)}")

    # TAB 3 — DEPLOY
    with tab3:
        st.header("🚢 Deploy to Dify")

        if not st.session_state.generated_dsl:
            st.info("ℹ Generate a DSL first before deploying")
        else:
            # Check validation
            if st.session_state.validation_results:
                is_valid, errors, _ = st.session_state.validation_results

                if not is_valid:
                    st.warning(
                        "⚠ Your DSL has validation issues. "
                        "It's recommended to fix them before deploying."
                    )
                    if st.checkbox("Deploy anyway (not recommended)"):
                        pass
                    else:
                        st.stop()

            # Dify integration
            if not dify_key or not dify_url:
                st.warning(
                    "⚠ Dify integration not configured. "
                    "Please provide API key and URL in the sidebar."
                )
                st.subheader("Manual Import Instructions")
                st.markdown("""
**To manually import to Dify:**

1. Download the generated DSL using the button in the Generate tab
2. Go to your Dify Studio
3. Click **Create Application**
4. Select **Import DSL File**
5. Upload the downloaded `.yml` file
6. Configure any required API keys and datasets
7. Test and publish your workflow
""")
            else:
                integration = DifyIntegration(dify_url, dify_key)

                st.subheader("Deploy Configuration")
                col1, col2 = st.columns(2)

                with col1:
                    app_name = st.text_input(
                        "Application Name (Optional)",
                        placeholder="Leave empty to use name from DSL",
                    )
                with col2:
                    st.info(f"🌐 Deploying to: {dify_url}")

                # Deploy button
                if st.button(
                    "🚢 Deploy to Dify", type="primary", use_container_width=True
                ):
                    logger.info("Starting deployment to Dify")

                    with st.spinner("Deploying to Dify..."):
                        result = integration.import_dsl(
                            st.session_state.generated_dsl,
                            app_name if app_name else None,
                        )

                    if result["success"]:
                        logger.info(
                            f"Deployment successful. App ID: {result.get('app_id', 'N/A')}"
                        )
                        st.success(result["message"])
                        st.balloons()
                        st.markdown(f"""
### ✅ Successfully Deployed!

**App ID:** `{result.get('app_id', 'N/A')}`

**Next Steps:**
1. Configure required API keys in Dify
2. Set up knowledge base datasets (if using RAG)
3. Test the workflow
4. Publish when ready

[🔗 Open in Dify]({result.get('app_url', dify_url)})
""")
                    else:
                        logger.error(f"Deployment failed: {result['message']}")
                        st.error(result["message"])
                        if "error" in result:
                            with st.expander("Error Details"):
                                st.code(result["error"])

                st.divider()

                # Show existing apps
                st.subheader("Your Dify Applications")
                if st.button("🔄 Refresh Apps List"):
                    apps_result = integration.get_apps()
                    if apps_result["success"]:
                        apps = apps_result["apps"]
                        if apps:
                            st.write(f"Total apps: {apps_result['total']}")
                            for app in apps[:5]:  # Show first 5
                                with st.container():
                                    col1, col2, col3 = st.columns([3, 1, 1])
                                    with col1:
                                        st.write(
                                            f"**{app.get('name', 'Unnamed')}**"
                                        )
                                        st.caption(
                                            f"Type: {app.get('mode', 'N/A')}"
                                        )
                                    with col2:
                                        st.caption(
                                            f"ID: {app.get('id', 'N/A')[:8]}..."
                                        )
                                    with col3:
                                        st.link_button(
                                            "Open",
                                            f"{dify_url}/app/{app.get('id')}",
                                        )
                        else:
                            st.info("No apps found")
                    else:
                        st.error("Failed to fetch apps")

    # TAB 4 — HISTORY
    with tab4:
        st.header("📜 Generation History")

        if not st.session_state.history:
            st.info("ℹ No generation history yet")
        else:
            st.write(f"Total generations: {len(st.session_state.history)}")

            for i, item in enumerate(reversed(st.session_state.history)):
                with st.expander(
                    f"🕐 {item['timestamp']} — {item['workflow_type'].title()} ({item['complexity']})",
                    expanded=(i == 0),
                ):
                    st.write(
                        f"**Request:** {item['request'][:200]}{'...' if len(item['request']) > 200 else ''}"
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "Generation Time",
                            f"{item['metadata']['generation_time']}s",
                        )
                    with col2:
                        st.metric(
                            "Tokens", item["metadata"].get("tokens_used", 0)
                        )
                    with col3:
                        model_label = item["metadata"]["model_used"]
                        st.metric("Model", model_label.split("-")[1].title())

                    if st.button(f"📂 Load this DSL", key=f"load_{i}"):
                        st.session_state.generated_dsl = item["dsl"]
                        st.session_state.generation_metadata = item["metadata"]
                        st.success("✅ DSL loaded!")
                        st.rerun()

                    st.download_button(
                        "⬇️ Download",
                        data=item["dsl"],
                        file_name=f"workflow_{item['timestamp'].replace(':', '-')}.yml",
                        mime="text/yaml",
                        key=f"download_{i}",
                    )

            st.divider()
            if st.button("🗑 Clear History"):
                st.session_state.history = []
                st.rerun()


if __name__ == "__main__":
    main()