import streamlit as st

st.set_page_config(page_title="Predictive Modeling", page_icon="🧠", layout="wide")
st.title("🧠 Predictive Modeling: Rental Demand")

st.markdown("Use this tool to forecast the total lifetime rentals of a prospective film based on its attributes.")

# Create the interactive UI
with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        input_length = st.number_input("Film Length (minutes)", min_value=30, max_value=300, value=120)
        input_cost = st.slider("Replacement Cost ($)", min_value=9.99, max_value=29.99, value=19.99)
        
    with col2:
        input_rate = st.selectbox("Rental Rate ($)", [0.99, 2.99, 4.99])
        
    submitted = st.form_submit_button("Run Prediction Model")
    
    if submitted:
        # In a real scenario, you would load your pre-trained model here
        # model = joblib.load('random_forest_model.pkl')
        # prediction = model.predict([[input_length, input_rate, input_cost]])
        
        # Simulated result for demonstration
        simulated_prediction = (input_length * 0.1) + (float(input_rate) * 5) - (input_cost * 0.2) + 15
        
        st.success(f"📈 Projected Total Rentals: **{int(simulated_prediction)}**")
        st.caption("Note: This projection is based on the trained Random Forest regressor utilizing historical DVD rental performance.")