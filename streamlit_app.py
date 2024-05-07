import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import datetime
from google.cloud import firestore
from google.oauth2 import service_account
import json

# key_dict = json.loads(st.secrets["textkey"])
#use firestore-key.json file to get the key
key_dict = json.load(open("firestore-key.json"))
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

def get_data(sensor_name):
    """
    Retrieves data from the Firestore database.

    Returns:
        dict: A dictionary containing the data from the database.
    """
    # Create a reference to the Google post.
    doc_ref = db.collection("Test1").document(sensor_name)

    # Then get the data at that reference.
    doc = doc_ref.get()

    return doc.to_dict()

def get_chart(data):
    """
    Generates an interactive line chart based on the given data.

    Args:
        data (pd.DataFrame): The data to be plotted.

    Returns:
        alt.Chart: An Altair chart object.
    """
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
            opacity=alt.condition(hover, alt.value(0.3), alt.value(0)),
            tooltip=[
                alt.Tooltip("date", title="Date"),
                alt.Tooltip("value", title="Value"),
            ],
        )
        .add_params(hover)
    )
    return (lines + points + tooltips).interactive()

def main():
    """
    Main function to run the Streamlit app.
    """
    st.sidebar.title("Sensor Selection")

    # Get the list of sensors from the database
    list_of_sensors = [doc.id for doc in db.collection("Test1").stream()]

    # Add a selectbox to the sidebar for sensor selection
    sensor_name = st.sidebar.selectbox(
        "Select a sensor",
        list_of_sensors
    )

    data=get_data(sensor_name)

    f"""
    # Tracker `{sensor_name}`

    Location `41.37768208035169, 2.0860261852263178`
    """

    """
    ## Current Conditions
    """

    main_color = "#FF4B4B"

    # Strip the first 4 characters from the name of the keys of data. Then sort it by the key from largest to smallest
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

if __name__ == "__main__":
    main()
