import streamlit as st
from PIL import Image
from styles import apply_global_styles 
 
 
apply_global_styles()

st.title("The Gardner") 


col1, col2 = st.columns(2)

with col1:
    if st.button("Plant List"):
        st.write("Navigate to Plant List")  

with col2:
    if st.button("Plant Health Checker"):
        st.write("Navigate to Plant Health Checker")  
