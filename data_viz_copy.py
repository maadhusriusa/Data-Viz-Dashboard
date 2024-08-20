import pandas as pd
import numpy as np
import yaml
from yaml.loader import SafeLoader
import plotly.express as px
import plotly.figure_factory as ff
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import streamlit as st
import streamlit_authenticator as stauth

credentials  = {
    "usernames": {
        "Strategy_fox": {
            "name": "Pradeep Kumar",
            "password": "$2b$12$WhHO9C/B9.ZsZguCpwijpeoI2LhY1qPz92VrYr.gA5Gc4wAGKiJz."
        }
    }
}


# Initialize Streamlit Authenticator without needing password_hasher
authenticator = stauth.Authenticate(
    credentials = credentials ,
    cookie_name="my_app",
    cookie_expiry_days=30,
    key='my_secret_key'
)

# Login UI
name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f"Hello, {name}!")
    # Your app content here
elif authentication_status is False:
    st.error("Username or password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")


