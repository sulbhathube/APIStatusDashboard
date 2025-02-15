import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import requests
import plotly.graph_objs as go
from datetime import datetime, timedelta

app = dash.Dash(__name__)

app.layout = html.Div([
    # Header
    html.Div([
        html.Div(id='datetime', style={'margin-left': '20px', 'font-size': '20px'}),
        html.H1("Status App", style={'textAlign': 'center', 'width': '100%'})
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between', 'padding': '10px', 'backgroundColor': '#0033a0', 'color': 'white'}),
    
    # Interval Component
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # Default to 1 minute
        n_intervals=0
    ),
    
    # Current Status and API Call Frequency
    html.Div([
        html.Div([
            html.H2("Current Status", style={'textAlign': 'center'}),
            html.Div(id='current-status', style={'textAlign': 'center', 'fontSize': '24px', 'padding': '10px', 'backgroundColor': '#e9ecef', 'margin': '10px 0', 'color': '#0033a0'})
        ], style={'flex': '1'}),
        html.Div([
            html.H2("Select API Call Frequency", style={'textAlign': 'center'}),
            dcc.Dropdown(
                id='api-frequency-dropdown',
                options=[
                    {'label': 'Every 1 minute', 'value': 60*1000},
                    {'label': 'Every 5 minutes', 'value': 5*60*1000},
                    {'label': 'Every 10 minutes', 'value': 10*60*1000}
                ],
                value=60*1000,
                clearable=False,
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'padding': '0 20px'})
    ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'space-between', 'padding': '10px', 'backgroundColor': '#f8f9fa'}),
    
    # Add API to Monitor
    html.Div([
        html.H2("Add API to Monitor", style={'textAlign': 'center'}),
        dcc.Input(id='api-input', type='text', placeholder='Enter curl command', style={'width': '80%', 'margin': '0 auto'}),
        html.Button('Add API', id='add-api-button', n_clicks=0, style={'margin-top': '10px', 'backgroundColor': '#0033a0', 'color': 'white'})
    ], style={'textAlign': 'center', 'margin-top': '20px'}),
    
    # Detailed Status
    html.Div([
        html.H2("Detailed Status", style={'textAlign': 'center'}),
        dash_table.DataTable(
            id='status-table',
            columns=[
                {'name': 'API', 'id': 'api'},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Response Time', 'id': 'response_time'},
                {'name': 'Timestamp', 'id': 'timestamp'}
            ],
            data=[],
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': '#0033a0',
                'fontWeight': 'bold',
                'color': 'white'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{status} = "success"'},
                    'backgroundColor': '#d4edda',
                    'color': 'black'
                },
                {
                    'if': {'filter_query': '{status} = "failure"'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black'
                }
            ]
        )
    ], style={'margin-top': '20px', 'padding': '0 20px'}),
    
    # Time Duration Dropdown
    html.Div([
        html.H2("Select Time Duration", style={'textAlign': 'center'}),
        dcc.Dropdown(
            id='time-duration-dropdown',
            options=[
                {'label': 'Last 1 hour', 'value': '1h'},
                {'label': 'Last 3 hours', 'value': '3h'},
                {'label': 'Last 6 hours', 'value': '6h'},
                {'label': 'Last 12 hours', 'value': '12h'},
                {'label': 'Last 24 hours', 'value': '24h'}
            ],
            value='24h',
            clearable=False,
            style={'width': '50%', 'margin': '0 auto'}
        )
    ], style={'margin-top': '20px', 'padding': '0 20px'}),
    
    # Status Count Graph
    html.Div([
        dcc.Graph(id='status-count-graph')
    ], style={'margin-top': '20px', 'padding': '0 20px'}),
    
    # Response Time Graph
    html.Div([
        dcc.Graph(id='response-time-graph')
    ], style={'margin-top': '20px', 'padding': '0 20px'}),
    
    # Uptime Percentage
    html.Div([
        html.H2("Uptime for the current quarter:", style={'textAlign': 'center'}),
        html.Div(id='uptime-percentage', style={'textAlign': 'center', 'fontSize': '24px', 'padding': '10px', 'backgroundColor': '#e9ecef', 'margin': '10px 0', 'color': '#0033a0'})
    ], style={'display': 'flex', 'justify-content': 'center'})
])

@app.callback(
    Output('interval-component', 'interval'),
    [Input('api-frequency-dropdown', 'value')]
)
def update_interval(frequency):
    return frequency

@app.callback(
    Output('datetime', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_datetime(n):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Current Date and Time: {now}"

@app.callback(
    [Output('current-status', 'children'),
     Output('status-table', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('add-api-button', 'n_clicks')],
    [State('api-input', 'value')]
)
def update_status_and_add_api(n_intervals, n_clicks, api_command):
    ctx = dash.callback_context

    if not ctx.triggered:
        return "No API added", []

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'add-api-button' and api_command:
        response = requests.post("http://127.0.0.1:8000/api/add", json={"command": api_command})
        if response.status_code == 200:
            return f"Added API: {api_command}", []
        else:
            return f"Error: {response.json()['detail']}", []

    # Update status for all APIs
    requests.post("http://127.0.0.1:8000/api/update_status")

    response = requests.get("http://127.0.0.1:8000/api/status")
    data = response.json()

    table_data = []
    for api, statuses in data.items():
        if statuses:
            latest_status = statuses[-1]
            table_data.append({
                'api': api,
                'status': latest_status['status'],
                'response_time': latest_status['response_time'],
                'timestamp': latest_status['timestamp']
            })

    latest_status = table_data[-1]['status'] if table_data else 'No data'

    return f"Horizon API Status: {latest_status}", table_data

@app.callback(
    Output('status-count-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-duration-dropdown', 'value')]
)
def update_status_count_graph(n, duration):
    response = requests.get("http://127.0.0.1:8000/api/status")
    data = response.json()

    # Filter data based on the selected time duration
    now = datetime.now()
    if duration == '1h':
        time_threshold = now - timedelta(hours=1)
    elif duration == '3h':
        time_threshold = now - timedelta(hours=3)
    elif duration == '6h':
        time_threshold = now - timedelta(hours=6)
    elif duration == '12h':
        time_threshold = now - timedelta(hours=12)
    else:
        time_threshold = now - timedelta(hours=24)

    try:
        filtered_data = []
        for api, statuses in data.items():
            filtered_data.extend([item for item in statuses if 'timestamp' in item and datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S') >= time_threshold])
    except ValueError as e:
        print(f"Error parsing timestamp: {e}")
        filtered_data = []

    statuses = [item['status'] for item in filtered_data]

    success_count = statuses.count("success")
    failure_count = statuses.count("failure")

    figure = {
        'data': [
            go.Bar(
                x=['Success', 'Failure'],
                y=[success_count, failure_count],
                name='Status Count'
            )
        ],
        'layout': go.Layout(
            title='Horizon API Status Count',
            xaxis={'title': 'Status'},
            yaxis={'title': 'Count'},
            barmode='group'
        )
    }

    return figure

@app.callback(
    Output('response-time-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('time-duration-dropdown', 'value')]
)
def update_response_time_graph(n, duration):
    response = requests.get("http://127.0.0.1:8000/api/status")
    data = response.json()

    # Filter data based on the selected time duration
    now = datetime.now()
    if duration == '1h':
        time_threshold = now - timedelta(hours=1)
    elif duration == '3h':
        time_threshold = now - timedelta(hours=3)
    elif duration == '6h':
        time_threshold = now - timedelta(hours=6)
    elif duration == '12h':
        time_threshold = now - timedelta(hours=12)
    else:
        time_threshold = now - timedelta(hours=24)

    try:
        filtered_data = []
        for api, statuses in data.items():
            filtered_data.extend([item for item in statuses if 'timestamp' in item and datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S') >= time_threshold])
    except ValueError as e:
        print(f"Error parsing timestamp: {e}")
        filtered_data = []

    response_times = [item['response_time'] for item in filtered_data]

    figure = {
        'data': [
            go.Scatter(
                x=list(range(len(response_times))),
                y=response_times,
                mode='lines+markers',
                name='Response Time'
            )
        ],
        'layout': go.Layout(
            title='Horizon API Response Time',
            xaxis={'title': 'API Calls'},
            yaxis={'title': 'Response Time (s)'}
        )
    }

    return figure

@app.callback(
    Output('uptime-percentage', 'children'),
    [Input('interval-component', 'n_intervals'),
     Input('time-duration-dropdown', 'value')]
)
def update_uptime_percentage(n, duration):
    response = requests.get("http://127.0.0.1:8000/api/status")
    data = response.json()

    # Filter data based on the selected time duration
    now = datetime.now()
    if duration == '1h':
        time_threshold = now - timedelta(hours=1)
    elif duration == '3h':
        time_threshold = now - timedelta(hours=3)
    elif duration == '6h':
        time_threshold = now - timedelta(hours=6)
    elif duration == '12h':
        time_threshold = now - timedelta(hours=12)
    else:
        time_threshold = now - timedelta(hours=24)

    try:
        filtered_data = []
        for api, statuses in data.items():
            filtered_data.extend([item for item in statuses if 'timestamp' in item and datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S') >= time_threshold])
    except ValueError as e:
        print(f"Error parsing timestamp: {e}")
        filtered_data = []

    statuses = [item['status'] for item in filtered_data]

    success_count = statuses.count("success")
    failure_count = statuses.count("failure")

    total_count = success_count + failure_count
    uptime_percentage = (success_count / total_count) * 100 if total_count > 0 else 0

    return f"{uptime_percentage:.2f}%"

if __name__ == '__main__':
    app.run_server(debug=True)
