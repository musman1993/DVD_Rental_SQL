import streamlit as st

st.set_page_config(
    page_title="DVD Rental Intelligence",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 DVD Rental Intelligence Hub")
st.markdown("""
Welcome to the internal data portal. Use the sidebar to navigate between:
* **📊 Analytics Dashboard:** Explore historical rental data, revenue, and inventory metrics.
* **🧠 Predictive Modeling:** Run our Random Forest model to forecast demand for new catalog entries.
""")

st.info("👈 Please select a tool from the sidebar to begin.")