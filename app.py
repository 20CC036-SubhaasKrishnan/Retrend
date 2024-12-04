from flask import Flask, request, render_template
import pandas as pd
from datetime import datetime, time

app = Flask(__name__)


# Helper function to find max time difference in a given range
def get_max_time_difference(timestamps):
    max_diff = pd.Timedelta(0)
    for i in range(1, len(timestamps)):
        diff = timestamps.iloc[i] - timestamps.iloc[i - 1]
        if diff > max_diff:
            max_diff = diff
    return max_diff


# Categorize timestamps into BH, NBH, and WE trends
def categorize_timestamps(df):
    df['Category'] = df['Timestamp'].apply(lambda x: categorize_time(x))
    return df


def categorize_time(timestamp):
    weekday = timestamp.weekday()
    hour = timestamp.time()

    if weekday < 5 and time(9, 0) <= hour < time(18, 0):
        return 'BH'
    if weekday < 5 and (hour >= time(18, 0) or hour < time(9, 0)):
        return 'NBH'
    if (weekday == 5 and hour >= time(18, 0)) or (weekday == 6) or (weekday == 0 and hour < time(9, 0)):
        return 'WE'
    return 'NBH'


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    results = None  # Ensure results is None initially
    error_message = None

    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        #  code to handle the csv file
        # then also i have handled files , is they are empty or not
        if uploaded_file and uploaded_file.filename.endswith('.csv'):
            try:
                # Parse the CSV file
                data = pd.read_csv(uploaded_file)
                if 'Timestamp' not in data.columns:
                    raise ValueError("CSV file must contain a 'Timestamp' column.")
                data['Timestamp'] = pd.to_datetime(data['Timestamp'], format='%d %b %Y, %H:%M:%S', errors='coerce')
                data = data.dropna(subset=['Timestamp'])  # Drop rows with invalid timestamps

                if data.empty:
                    raise ValueError("No valid timestamps found in the file.")

                # Categorize timestamps and calculate max time differences
                data = categorize_timestamps(data)
                results = {}
                for category in ["BH", "NBH", "WE"]:
                    timestamps = data.loc[data['Category'] == category, 'Timestamp'].sort_values()
                    if len(timestamps) > 1:
                        max_diff = get_max_time_difference(timestamps)
                        results[category] = f"Maximum time difference in {category} trend: {max_diff.total_seconds() / 60:.2f} minutes"
                    else:
                        results[category] = f"Not enough data points for {category} trend"
            except Exception as e:
                error_message = f"Error processing file: {e}"
        else:
            error_message = "No file was uploaded or the file is not a CSV. Please select a valid CSV file."

    return render_template('index.html', results=results, error_message=error_message)


if __name__ == '__main__':
    app.run(debug=True)