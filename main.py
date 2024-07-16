import plotly.express as px
import streamlit as st
import pandas as pd
from datetime import datetime

# Authentication setup
def login(username, password):
    if username == "quality" and password == "ice cream":
        return True
    else:
        return False

# Define session state variables for login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''
if 'password' not in st.session_state:
    st.session_state['password'] = ''

# Login form
if not st.session_state['logged_in']:
    st.title("Login")
    st.session_state['username'] = st.text_input("Username")
    st.session_state['password'] = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(st.session_state['username'], st.session_state['password']):
            st.session_state['logged_in'] = True
            st.experimental_rerun()  # Refresh to reflect login status
        else:
            st.error("Invalid username or password")
else:
    # Main application after login
    st.sidebar.title("Sidebar")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.experimental_rerun()  # Refresh to reflect logout status

    st.title('Cleanroom Pressure Differential Monitoring')

    # Load the dataset from URL
    url = 'https://raw.githubusercontent.com/Steripack/clr/main/ForExperiment24.csv'  # Replace with the actual URL
    df = pd.read_csv(url, parse_dates=['DPV_timestamp'], dayfirst=True)

    # Manually convert 'DPV_timestamp' to datetime
    df['DPV_timestamp'] = pd.to_datetime(df['DPV_timestamp'], errors='coerce')

    # Define a list of Irish bank holidays for 2024
    irish_bank_holidays = [
        '2024-01-01',  # New Year's Day
        '2024-03-17',  # St. Patrick's Day
        '2024-04-01',  # Easter Monday
        '2024-05-06',  # May Day (First Monday in May)
        '2024-06-03',  # June Bank Holiday (First Monday in June)
        '2024-08-05',  # August Bank Holiday (First Monday in August)
        '2024-10-28',  # October Bank Holiday (Last Monday in October)
        '2024-12-25',  # Christmas Day
        '2024-12-26'  # St. Stephen's Day (Boxing Day)
    ]

    # Convert bank holidays to datetime
    irish_bank_holidays = pd.to_datetime(irish_bank_holidays)

    # Define spec limits for each column
    spec_limits = {
        'DPV_Messanin': {'upper': 50, 'lower': 20},
        'DPV_Gowning': {'upper': 13, 'lower': 7},
        'DPV_Good_In': {'upper': 13, 'lower': 7},
        'DPV_Washdown': {'upper': 5, 'lower': -5}
    }

    # Function to filter data
    def filter_data(df, start_date, end_date):
        # Convert start_date and end_date to datetime
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filter data between start and end date
        df_filtered = df[(df['DPV_timestamp'] >= start_date) & (df['DPV_timestamp'] <= end_date)]

        # Exclude weekends
        df_filtered = df_filtered[df_filtered['DPV_timestamp'].dt.weekday < 5]

        # Exclude bank holidays
        df_filtered = df_filtered[~df_filtered['DPV_timestamp'].dt.normalize().isin(irish_bank_holidays)]

        # Exclude specific break periods and filter for 15-minute intervals
        df_filtered = df_filtered[
            (df_filtered['DPV_timestamp'].dt.hour >= 8) & (df_filtered['DPV_timestamp'].dt.hour <= 16) &
            ~((df_filtered['DPV_timestamp'].dt.hour == 10) & (df_filtered['DPV_timestamp'].dt.minute >= 30)) &
            ~((df_filtered['DPV_timestamp'].dt.hour == 11) & (df_filtered['DPV_timestamp'].dt.minute < 0)) &
            ~((df_filtered['DPV_timestamp'].dt.hour == 13) & (df_filtered['DPV_timestamp'].dt.minute == 0))]
        df_filtered = df_filtered[df_filtered['DPV_timestamp'].dt.minute % 15 == 0]

        return df_filtered

    # Function to plot data points with spec limits, average, and ±3*SD using Plotly
    def plot_data_with_limits(data, column_name, title, upper_spec_limit, lower_spec_limit):
        fig = px.line(data, x=data.index, y=column_name, title=title, labels={'x': 'Timestamp', 'y': column_name},
                      line_shape='linear')

        # Calculate average and standard deviation
        avg = data[column_name].mean()
        std_dev = data[column_name].std()

        # Add horizontal lines for spec limits, average, and ±3*SD
        fig.add_hline(y=upper_spec_limit, line_dash="dash", line_color="red", annotation_text="Upper Spec Limit", annotation_position="top left")
        fig.add_hline(y=lower_spec_limit, line_dash="dash", line_color="red", annotation_text="Lower Spec Limit", annotation_position="top left")
        fig.add_hline(y=avg, line_dash="dash", line_color="green", annotation_text="Average", annotation_position="top left")
        fig.add_hline(y=avg + 3 * std_dev, line_dash="dash", line_color="orange", annotation_text="+3*SD", annotation_position="top left")
        fig.add_hline(y=avg - 3 * std_dev, line_dash="dash", line_color="orange", annotation_text="-3*SD", annotation_position="top left")

        # Display plot
        st.plotly_chart(fig)

    # Function to update plots based on date range
    def update_plots(start_date, end_date):
        filtered_data = filter_data(df, start_date, end_date)
        filtered_data.set_index('DPV_timestamp', inplace=True)

        for column in spec_limits:
            plot_data_with_limits(filtered_data, column, f'{column} Pressure Differential', spec_limits[column]['upper'],
                                  spec_limits[column]['lower'])

    # Create date pickers for start and end date
    start_date = st.date_input('Start Date', value=pd.to_datetime('2024-03-01'))
    end_date = st.date_input('End Date', value=pd.to_datetime('2024-06-30'))

    # Create button to update plots
    if st.button('Update Plots'):
        update_plots(start_date, end_date)
