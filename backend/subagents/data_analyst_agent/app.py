import streamlit as st
import tempfile
import sys
import pathlib
from dotenv import load_dotenv

# Load environment variables from local .env
env_path = pathlib.Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure package imports work when running app directly
pkg_root = pathlib.Path(__file__).resolve().parent.parent
if str(pkg_root) not in sys.path:
    sys.path.append(str(pkg_root))

from data_analyst_agent.graph import run_data_analyst_agent

st.set_page_config(page_title="Data Analyst Agent Tester", layout="wide")

st.title("🧪 Data Analyst Subagent — Test Dashboard Generator")

st.write(
    """
    Upload a **CSV** or **Excel** file and the Data Analyst Agent will:
    1. Generate Python code via LLM  
    2. Execute it in a sandbox  
    3. Produce an interactive **HTML dashboard**  
    """
)

uploaded = st.file_uploader("Upload CSV or Excel file", type=["csv", "xls", "xlsx"])

user_request = st.text_area(
    "What do you want the dashboard to do?",
    "Create a simple EDA dashboard with summary statistics and interactive charts",
    height=100,
)

run_btn = st.button("Run Data Analyst Agent")

if run_btn:
    if not uploaded:
        st.error("Please upload a file before running.")
        st.stop()

    # Save uploaded file to a temporary location
    suffix = "." + uploaded.name.split(".")[-1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(uploaded.read())
    tmp.flush()

    st.info("Running agent... please wait. ⏳")

    try:
        final_state = run_data_analyst_agent(tmp.name, user_request)
    except Exception as e:
        st.error(f"Agent execution failed: {e}")
        st.stop()

    # Display logs
    st.subheader("Agent Logs")
    st.json(final_state.get("logs", []))

    # Check for error
    if final_state.get("error"):
        st.error(f"Agent Error: {final_state['error']}")
        st.stop()

    # Output HTML content
    html = final_state.get("html_content")
    if html:
        st.subheader("Generated Dashboard (HTML Preview)")
        
        # Show in iframe
        st.components.v1.html(html, height=800, scrolling=True)

        st.success("Dashboard was generated successfully!")
    else:
        st.warning("No HTML output found.")
