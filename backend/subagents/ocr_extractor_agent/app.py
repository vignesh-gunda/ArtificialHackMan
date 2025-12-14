# streamlit_app.py
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import asyncio
import os
from dotenv import load_dotenv
from agents.extraction_agent import build_extraction_graph, AgentState
from services.ocr_service import DeepSeekOCRService
 
load_dotenv()

# Page config
st.set_page_config(
    page_title="Audit Extraction Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #00a67e; }
    .finding-card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
    .critical { border-left: 5px solid #d32f2f; }
    .high { border-left: 5px solid #f57c00; }
    .medium { border-left: 5px solid #fbc02d; }
    .low { border-left: 5px solid #388e3c; }
    .review-needed { background-color: #fff3cd; }
</style>
""", unsafe_allow_html=True)

# Session state
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = []
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/clipboard.png", width=80)
    st.title("Audit Extraction Agent")
    
    st.subheader("Configuration")
    confidence_threshold = st.slider(
        "Confidence Threshold",
        min_value=0.0,
        max_value=1.0,
        value=float(os.getenv("CONFIDENCE_THRESHOLD", 0.7)),
        step=0.05
    )
    
    max_retries = st.number_input(
        "Max Retry Attempts",
        min_value=0,
        max_value=5,
        value=int(os.getenv("MAX_RETRY_ATTEMPTS", 2))
    )
    
    if st.button("🔄 Refresh Results"):
        load_existing_results()

def load_existing_results():
    """Load all previously extracted results from outputs folder"""
    output_dir = Path("outputs/extracted_findings")
    if not output_dir.exists():
        return []
    
    results = []
    for json_file in output_dir.glob("*.json"):
        try:
            with open(json_file) as f:
                data = json.load(f)
                results.append(data)
        except:
            continue
    
    st.session_state.extraction_results = results
    return results

def display_finding_card(finding, index):
    """Display a single finding in a card format"""
    severity_class = finding.get("severity", "Info").lower()
    needs_review = finding.get("confidence_score", 0) < confidence_threshold
    
    card_class = f"finding-card {severity_class}"
    if needs_review:
        card_class += " review-needed"
    
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**#{finding.get('finding_number', 'N/A')}** - {finding.get('title', 'No Title')}")
    with col2:
        severity = finding.get("severity", "Unknown")
        st.markdown(f"Severity: `{severity}`")
    with col3:
        conf = finding.get("confidence_score", 0)
        st.markdown(f"Confidence: `{conf:.2f}`")
    
    # Content
    with st.expander("View Details", expanded=False):
        tab1, tab2, tab3, tab4 = st.tabs(["Description", "Recommendation", "Metadata", "Raw JSON"])
        
        with tab1:
            st.markdown("**Description:**")
            st.write(finding.get("description", "N/A"))
        
        with tab2:
            st.markdown("**Recommendation:**")
            st.write(finding.get("recommendation", "N/A"))
        
        with tab3:
            st.json({
                "Status": finding.get("status"),
                "Impact": finding.get("impact"),
                "Likelihood": finding.get("likelihood"),
                "Repository": finding.get("repository_url"),
                "Commit ID": finding.get("commit_id"),
                "Additional Fields": finding.get("additional_fields", {})
            })
        
        with tab4:
            st.json(finding)
    
    st.markdown('</div>', unsafe_allow_html=True)

async def process_uploaded_file(uploaded_file):
    """Process a single uploaded file"""
    # Save uploaded file
    temp_path = Path("temp_upload.pdf")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Initialize services
    ocr_service = DeepSeekOCRService()
    agent = build_extraction_graph()
    
    # OCR Phase
    with st.spinner("🔍 Running OCR..."):
        ocr_result = await ocr_service.process_pdf(str(temp_path))
        if ocr_result["status"] == "failed":
            st.error(f"OCR Failed: {ocr_result['error']}")
            return None
    
    # Extraction Phase
    with st.spinner("🤖 AI extraction in progress..."):
        initial_state = {
            "pdf_path": str(temp_path),
            "markdown_content": ocr_result["markdown"],
            "extraction_result": None,
            "validation_errors": [],
            "retry_count": 0,
            "needs_retry": False
        }
        
        final_state = await agent.ainvoke(initial_state)
        result = final_state["extraction_result"]
    
    # Cleanup
    temp_path.unlink()
    
    return result

# Main dashboard
st.title("📋 Audit Extraction Monitoring Dashboard")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload & Process", "📊 Results", "⚠️ Review Queue", "📈 Analytics"])

with tab1:
    st.header("Upload Audit Report")
    
    uploaded_file = st.file_uploader(
        "Drop PDF file here",
        type=["pdf"],
        help="Upload a single audit report PDF for extraction"
    )
    
    if uploaded_file and not st.session_state.processing:
        if st.button("🚀 Start Extraction", type="primary"):
            st.session_state.processing = True
            
            # Process file
            result = asyncio.run(process_uploaded_file(uploaded_file))
            
            if result:
                st.success(f"✅ Extraction complete! Found {len(result.findings)} findings")
                st.session_state.extraction_results.append(result.model_dump())
            
            st.session_state.processing = False
    
    if st.session_state.processing:
        st.info("Processing in progress...")

with tab2:
    st.header("Extraction Results")
    
    if not st.session_state.extraction_results:
        st.info("No results yet. Upload a PDF to get started.")
    else:
        # File selector
        files = [r.get("filename", f"Result {i}") for i, r in enumerate(st.session_state.extraction_results)]
        selected_file = st.selectbox("Select Report", files)
        
        # Get selected result
        result_idx = files.index(selected_file)
        result = st.session_state.extraction_results[result_idx]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Findings", len(result.get("findings", [])))
        with col2:
            avg_conf = sum(f.get("confidence_score", 0) for f in result.get("findings", [])) / len(result.get("findings", 1))
            st.metric("Avg Confidence", f"{avg_conf:.2f}")
        with col3:
            critical_count = sum(1 for f in result.get("findings", []) if f.get("severity") == "Critical")
            st.metric("Critical", critical_count)
        with col4:
            review_needed = sum(1 for f in result.get("findings", []) if f.get("confidence_score", 0) < confidence_threshold)
            st.metric("Needs Review", review_needed)
        
        # Display findings
        st.subheader("Findings")
        for idx, finding in enumerate(result.get("findings", [])):
            display_finding_card(finding, idx)

with tab3:
    st.header("Human Review Queue")
    
    # Filter findings that need review
    all_findings = []
    for result in st.session_state.extraction_results:
        for finding in result.get("findings", []):
            if finding.get("confidence_score", 0) < confidence_threshold or finding.get("requires_human_review"):
                all_findings.append({
                    **finding,
                    "source_file": result.get("filename")
                })
    
    if not all_findings:
        st.success("✅ No findings require human review!")
    else:
        st.warning(f"⚠️ {len(all_findings)} findings need review")
        
        for finding in all_findings:
            with st.container():
                display_finding_card(finding, 0)
                
                # Review actions
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if st.button("✅ Approve", key=f"approve_{finding['finding_number']}"):
                        st.success("Approved!")
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{finding['finding_number']}"):
                        st.info("Edit mode would open here")
                with col3:
                    st.markdown(f"Source: `{finding['source_file']}`")

with tab4:
    st.header("Analytics & Statistics")
    
    if st.session_state.extraction_results:
        # Create DataFrame for analysis
        all_findings = []
        for result in st.session_state.extraction_results:
            for finding in result.get("findings", []):
                all_findings.append({
                    "File": result.get("filename"),
                    "Finding Number": finding.get("finding_number"),
                    "Severity": finding.get("severity"),
                    "Confidence": finding.get("confidence_score"),
                    "Status": finding.get("status"),
                    "Needs Review": finding.get("confidence_score", 0) < confidence_threshold
                })
        
        df = pd.DataFrame(all_findings)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Findings by Severity")
            severity_counts = df["Severity"].value_counts()
            st.bar_chart(severity_counts)
        
        with col2:
            st.subheader("Confidence Distribution")
            # Create histogram data manually
            confidence_data = df["Confidence"].dropna()
            if len(confidence_data) > 0:
                import numpy as np
                hist_data, bin_edges = np.histogram(confidence_data, bins=10)
                bin_labels = [f"{bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}" for i in range(len(hist_data))]
                hist_df = pd.DataFrame({"Range": bin_labels, "Count": hist_data})
                st.bar_chart(hist_df.set_index("Range"))
            else:
                st.info("No confidence data available")
        
        # Detailed table
        st.subheader("Detailed Results")
        st.dataframe(df, use_container_width=True)
        
        # Export options
        st.subheader("Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "audit_findings.csv",
                "text/csv"
            )
        
        with col2:
            # Convert extraction results to JSON-serializable format
            def serialize_datetime(obj):
                if hasattr(obj, 'isoformat'):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            json_data = json.dumps(st.session_state.extraction_results, indent=2, default=serialize_datetime)
            st.download_button(
                "📥 Download JSON",
                json_data,
                "audit_findings.json",
                "application/json"
            )
    else:
        st.info("No data available for analytics")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("""
**Audit Extraction Agent** v1.0

Built with:
- DeepSeek-OCR (Replicate)
- LangGraph
- Streamlit
""")