from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import pg8000.native as pg
import os
from dotenv import load_dotenv

load_dotenv()

con = pg.Connection(
        os.getenv('db_user') ,
        password=os.getenv('db_passwd'), 
        host=os.getenv('db_host'), 
        port=os.getenv('db_port'), 
        database=os.getenv('db_database'))

app = Dash()

app.layout = html.Div([
    html.H1("Air quality measurements"),
    html.Div([
        dbc.Row([
            dbc.Label("Parameter", html_for="parameter", width=2),
            dbc.Col(
                dcc.RadioItems(id='parameter', inline=True, options=[
                {'label': 'Particles <= 10µm', 'value': 'pm10'},
                {'label': 'Particles <= 25µm', 'value': 'pm25'},
                {'label': 'Carbon monoxide (Co)', 'value': 'co'},
                {'label': 'Sulfur dioxide (So²)', 'value': 'so2'},
                {'label': 'Nitrogen dioxide (No²)', 'value': 'no2'},
                {'label': 'Ozone', 'value': 'o3'},],
                value='pm10', style={'margin-bottom': '10px'}),
            )
        ]),
        dbc.Row([
            dbc.Label("Time interval", html_for="hours", width=2),
            dbc.Col(
                dcc.Slider(0, 24, 3, value=3, id='hours')
            )
        ]),
        dbc.Row([
            dcc.Graph(figure={}, id='map-output', 
                        style = {'width':'100%', 'height':'80vh'})
        ])
    ])
])

px.set_mapbox_access_token(open(".mapbox_token").read())

@callback(
    Output(component_id='map-output', component_property='figure'),
    Input(component_id='parameter', component_property='value'),
        Input(component_id='hours', component_property='value')
)

def update_map(parameter, hours):
    db_data = con.run("""SELECT r.location_id, 
                      l.location, 
                      r.parameter, 
                      r.unit, 
                      l.lat::numeric AS lat, 
                      l.lon::numeric AS lon, 
                      avg(r.value) AS avg, 
                      concat(to_char(avg(r.value), 'FM999.99'::text), ' ', r.unit) AS reading, 
                      count(r.value) as nmbr_readings 
                      FROM \"Readings\" r JOIN \"Locations\" l ON r.location_id = l.id 
                      WHERE parameter = :p 
                      AND timestamp >= now() - INTERVAL '"""+ str(hours) + """ hours' 
                      GROUP BY r.location_id, l.location, r.parameter, r.unit, l.lat, l.lon""",
                      p=parameter)
    df = pd.DataFrame(db_data, columns=[c['name'] for c in con.columns])
    fig = px.scatter_mapbox(df, hover_name="location", custom_data=["location","reading", "nmbr_readings"],lat="lat", lon="lon", color="avg", color_continuous_scale=px.colors.diverging.RdYlGn_r, zoom=7, )
    fig.update_traces(mode="markers", hovertemplate='<b>%{customdata[0]}</b><br />Average Reading: %{customdata[1]}<br />Nmbr of readings: %{customdata[2]}')
    fig.update_layout(margin={"r":10,"t":10,"l":10,"b":0})
    return fig

if __name__ == '__main__': 
    app.run(debug=True)