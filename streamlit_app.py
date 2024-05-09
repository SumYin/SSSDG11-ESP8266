import numpy as np
import pandas as pd
import streamlit as st
import datetime
from google.cloud import firestore
from google.oauth2 import service_account
import plotly.express as px
import plotly.graph_objects as go
import json

key_dict = json.loads(st.secrets["textkey"])
#use firestore-key.json file to get the key
# key_dict = json.load(open("firestore-key.json"))
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds)

temperature_color="#4169E1"
humidity_color="#FF4B4B"

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
def create_chart_data(sorted_data):
    new_chart_data = [{'date': datetime.datetime.fromtimestamp(int(ts)), 
         'temperature': values[0], 
         'humidity': values[1]} for ts, values in sorted_data.items()]
    return pd.DataFrame(new_chart_data)

def create_line_chart(chart_data):
    chart_data = chart_data.melt(id_vars='date', var_name='type', value_name='value')
    color_dict = {'temperature': temperature_color, 'humidity': humidity_color}
    fig = px.line(chart_data, x="date", y="value", color='type', title='Temperature and Humidity over Time', color_discrete_map=color_dict)
    return fig

def create_histogram(df, column, title, color):
    fig = px.histogram(df, x=column, histnorm='probability density', color_discrete_sequence=[color], marginal="violin")
    fig.update_layout(
        title=title,
        xaxis_title=column,
        yaxis_title="Frequency",
    )
    return fig

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


    f"""
    # Tracker `{sensor_name}`
    Fetched At: `{datetime.datetime.now()}`
    """

    """
    ## Current Conditions
    """

    #reload button before data to refresh the data
    st.button('Update Data')
    raw_data=get_data(sensor_name)


    # Strip the first 4 characters from the name of the keys of data. Then sort it by the key from largest to smallest
    sorted_data = {k[4:]: v for k, v in sorted(raw_data.items(), key=lambda item: item[0], reverse=True)}
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
    ## Historial Conditions
    #### Line Chart
    """

    chart_data = create_chart_data(sorted_data)
    fig = create_line_chart(chart_data)
    st.plotly_chart(fig)
    fig = create_histogram(chart_data, "temperature", "Distribution of Temperatures", temperature_color)
    st.plotly_chart(fig)
    fig = create_histogram(chart_data, "humidity", "Distribution of Humidity", humidity_color)
    st.plotly_chart(fig)
    st.dataframe(chart_data, use_container_width=True)

if __name__ == "__main__":
    main()
