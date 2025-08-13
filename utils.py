import streamlit as st

def apply_style_and_logo():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat&display=swap');
        html, body, [class*="css"] {
            font-family: 'Montserrat', sans-serif;
        }
        </style>
        """, unsafe_allow_html=True)

    #st.sidebar.image("logo-wavetransition_long.png", use_column_width=True)
    
    st.sidebar.image("logo-wavetransition_long.png", use_container_width=True)