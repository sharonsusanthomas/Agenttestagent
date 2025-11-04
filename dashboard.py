import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="Test Results Dashboard",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- CUSTOM CSS -------------------
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .pass-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .fail-card {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    .partial-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------- LOAD DATA -------------------
@st.cache_data
def load_comparison_data():
    """Load comparison report from JSON file"""
    report_path = "outputs/comparison_report.json"
    
    if not os.path.exists(report_path):
        return None
    
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------------- MAIN DASHBOARD -------------------
def main():
    st.title("🧪 Test Results Dashboard")
    st.markdown("---")
    
    # Load data
    report = load_comparison_data()
    
    if report is None:
        st.error("❌ No comparison report found!")
        st.info("💡 Run `python compare_results.py` first to generate test results.")
        return
    
    # Extract data
    summary = report.get("summary", {})
    comparisons = report.get("comparisons", [])
    timestamp = report.get("timestamp", "")
    method = report.get("comparison_method", "Unknown")
    
    # ------------------- SIDEBAR -------------------
    with st.sidebar:
        st.header("📊 Report Info")
        st.write(f"**Timestamp:** {timestamp[:19]}")
        st.write(f"**Method:** {method}")
        st.write(f"**Total Tests:** {summary.get('total_tests', 0)}")
        
        st.markdown("---")
        
        # Filter options
        st.header("🔍 Filters")
        status_filter = st.multiselect(
            "Filter by Status",
            options=["PASS", "PARTIAL", "FAIL"],
            default=["PASS", "PARTIAL", "FAIL"]
        )
        
        min_score = st.slider(
            "Minimum Similarity Score",
            min_value=0,
            max_value=100,
            value=0,
            step=5
        )
        
        st.markdown("---")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # ------------------- TOP METRICS -------------------
    st.header("📈 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Tests",
            value=summary.get("total_tests", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Passed",
            value=summary.get("passed", 0),
            delta=f"{summary.get('pass_rate', 0)}%"
        )
    
    with col3:
        st.metric(
            label="Failed",
            value=summary.get("failed", 0),
            delta=f"-{100 - summary.get('pass_rate', 0):.1f}%",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Pass Rate",
            value=f"{summary.get('pass_rate', 0)}%",
            delta=None
        )
    
    st.markdown("---")
    
    # ------------------- CHARTS -------------------
    st.header("📊 Visualizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart - Pass/Fail distribution
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Passed', 'Failed'],
            values=[summary.get('passed', 0), summary.get('failed', 0)],
            hole=0.4,
            marker_colors=['#28a745', '#dc3545']
        )])
        fig_pie.update_layout(
            title="Test Results Distribution",
            height=350
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart - Similarity scores
        df = pd.DataFrame(comparisons)
        fig_bar = px.bar(
            df,
            x='test_id',
            y='similarity_score',
            color='status',
            color_discrete_map={'PASS': '#28a745', 'PARTIAL': '#ffc107', 'FAIL': '#dc3545'},
            title="Similarity Scores by Test",
            labels={'test_id': 'Test ID', 'similarity_score': 'Similarity Score (%)'}
        )
        fig_bar.update_layout(height=350)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("---")
    
    # ------------------- DETAILED RESULTS TABLE -------------------
    st.header("📋 Detailed Test Results")
    
    # Filter data
    filtered_comparisons = [
        c for c in comparisons
        if c['status'] in status_filter and c['similarity_score'] >= min_score
    ]
    
    if not filtered_comparisons:
        st.warning("No tests match the current filters.")
        return
    
    # Create DataFrame
    df_display = pd.DataFrame(filtered_comparisons)
    df_display = df_display[['test_id', 'question', 'expected_answer', 'actual_answer', 'similarity_score', 'status']]
    df_display.columns = ['ID', 'Question', 'Expected', 'Actual', 'Score (%)', 'Status']
    
    # Style the dataframe
    def color_status(val):
        if val == 'PASS':
            return 'background-color: #d4edda'
        elif val == 'PARTIAL':
            return 'background-color: #fff3cd'
        else:
            return 'background-color: #f8d7da'
    
    styled_df = df_display.style.applymap(color_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True, height=400)
    
    st.markdown("---")
    
    # ------------------- INDIVIDUAL TEST CARDS -------------------
    st.header("🔍 Test Case Details")
    
    tabs = st.tabs(["✅ Passed", "⚠️ Partial", "❌ Failed"])
    
    # Passed tests
    with tabs[0]:
        passed_tests = [c for c in filtered_comparisons if c['status'] == 'PASS']
        if passed_tests:
            for test in passed_tests:
                with st.expander(f"Test #{test['test_id']}: {test['question'][:50]}..."):
                    st.markdown(f"""
                    <div class="pass-card">
                        <h4>✅ Test #{test['test_id']} - PASSED</h4>
                        <p><strong>Question:</strong> {test['question']}</p>
                        <p><strong>Expected:</strong> {test['expected_answer']}</p>
                        <p><strong>Actual:</strong> {test['actual_answer']}</p>
                        <p><strong>Similarity Score:</strong> {test['similarity_score']}%</p>
                        <p><strong>Reasoning:</strong> {test.get('reasoning', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No passed tests match the filters.")
    
    # Partial tests
    with tabs[1]:
        partial_tests = [c for c in filtered_comparisons if c['status'] == 'PARTIAL']
        if partial_tests:
            for test in partial_tests:
                with st.expander(f"Test #{test['test_id']}: {test['question'][:50]}..."):
                    st.markdown(f"""
                    <div class="partial-card">
                        <h4>⚠️ Test #{test['test_id']} - PARTIAL</h4>
                        <p><strong>Question:</strong> {test['question']}</p>
                        <p><strong>Expected:</strong> {test['expected_answer']}</p>
                        <p><strong>Actual:</strong> {test['actual_answer']}</p>
                        <p><strong>Similarity Score:</strong> {test['similarity_score']}%</p>
                        <p><strong>Reasoning:</strong> {test.get('reasoning', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No partial tests match the filters.")
    
    # Failed tests
    with tabs[2]:
        failed_tests = [c for c in filtered_comparisons if c['status'] == 'FAIL']
        if failed_tests:
            for test in failed_tests:
                with st.expander(f"Test #{test['test_id']}: {test['question'][:50]}..."):
                    st.markdown(f"""
                    <div class="fail-card">
                        <h4>❌ Test #{test['test_id']} - FAILED</h4>
                        <p><strong>Question:</strong> {test['question']}</p>
                        <p><strong>Expected:</strong> {test['expected_answer']}</p>
                        <p><strong>Actual:</strong> {test['actual_answer']}</p>
                        <p><strong>Similarity Score:</strong> {test['similarity_score']}%</p>
                        <p><strong>Reasoning:</strong> {test.get('reasoning', 'N/A')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.success("🎉 No failed tests!")
    
    st.markdown("---")
    
    # ------------------- DOWNLOAD REPORT -------------------
    st.header("📥 Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download JSON
        json_str = json.dumps(report, indent=2)
        st.download_button(
            label="📄 Download JSON Report",
            data=json_str,
            file_name=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        # Download CSV
        csv_data = df_display.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV Report",
            data=csv_data,
            file_name=f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

if __name__ == "__main__":
    main()