import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import datetime
from google.cloud import firestore
from google.oauth2 import service_account
import json
# Add a selectbox to the sidebar:
sensor_name = st.sidebar.selectbox(
    "Select a sensor",
    ("Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho", "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega")
)

def get_data():
    # Authenticate to Firestore with the JSON account key.
    # db = firestore.Client.from_service_account_json("firestore-key.json")
    key_dict = json.loads(st.secrets["textkey"])
    creds = service_account.Credentials.from_service_account_info(key_dict)
    db = firestore.Client(credentials=creds, project="streamlit-reddit")
    # Create a reference to the Google post.
    doc_ref = db.collection("Test1").document("Location1")

    # Then get the data at that reference.
    doc = doc_ref.get()

    return doc.to_dict()

data=get_data()
f"""
# Tracker `{sensor_name}`

Location `41.37768208035169, 2.0860261852263178`
"""

"""
## Current Conditions
"""

main_color = "#FF4B4B"


#strip the first 4 characters from the name of the keys of data. then sort it by the key from larges to smallest
sorted_data = {k[4:]: v for k, v in sorted(data.items(), key=lambda item: item[0], reverse=True)}
values_list = list(sorted_data.values())

# Get the first and second last values
current_temp = values_list[0][0]
second_last_temp = values_list[1][0]
temp_difference = current_temp - second_last_temp

current_humidity = values_list[0][1]
second_last_humidity = values_list[1][1]
humidity_difference = current_humidity - second_last_humidity

col1, col2, col3 = st.columns(3)
col1.metric("Temperature", f"{current_temp} °C", f"{temp_difference} °C")
col2.metric("Humidity", f"{current_humidity}%", f"{humidity_difference}%")

"""
## Sensor History
"""

def get_chart(data):
    hover = alt.selection_point(
        fields=["date"],
        nearest=True,
        on="mouseover",
        empty=False,
    )

    lines = (
        alt.Chart(data)
        .mark_line()
        .encode(
            x="date",
            y="value",
            color="type",
        )
    )
    # Draw points on the line, and highlight based on selection
    points = lines.transform_filter(hover).mark_circle(size=65)

    # Draw a rule at the location of the selection
    tooltips = (
        alt.Chart(data)
        .mark_rule()
        .encode(
            x="date:T",
            y="value",
            # y2="humidity",
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("date", title="Date"),
                alt.Tooltip("value", title="Value"),
                # alt.Tooltip("value", title="Humidity"),
            ],
        )
        .add_params(hover)
    )
    return (lines + points + tooltips).interactive()

# Prepare data for chart
# Create a single DataFrame for both temperature and humidity
data = [{'date': datetime.datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S'), 
         'temperature': values[0], 
         'humidity': values[1]} for ts, values in sorted_data.items()]

chart_data = pd.DataFrame(data)

# Melt the DataFrame to have a 'type' column
chart_data = chart_data.melt(id_vars='date', var_name='type', value_name='value')

chart = get_chart(chart_data)
st.altair_chart(
    (chart).interactive(),
    use_container_width=True
)


# st.button("Refresh")
# data=get_data()