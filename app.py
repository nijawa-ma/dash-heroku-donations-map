from dash import Dash, callback, html, dcc, Input, Output, State
import plotly.express as px
#import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import matplotlib as mpl
import gunicorn                     #whilst your local machine's webserver doesn't need this, Heroku's linux webserver (i.e. dyno) does. I.e. This is your HTTP server
from whitenoise import WhiteNoise   #for serving static files on Heroku
import json

# Instantiate dash app
app = Dash(__name__)

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server 

#Import counties polygons as json
with open(r'gz_2010_us_050_00_20m.json', 'r') as f:
    counties = json.load(f)

#Create and append FIPS codes to the counties in the json data
for feature in counties['features']:
    state_code = feature['properties']['STATE']
    county_code = feature['properties']['COUNTY']
    # Ensure leading zeros are preserved when necessary
    fips_code = f"{state_code}{county_code.zfill(3)}"
    feature['properties']['FIPS'] = fips_code

#Load the donations data and county information
df = pd.read_csv(r'DATA FOR APP v2.csv', dtype = {'FIPS': str})
states = sorted(df['state'].unique())
state_options = [{'label': 'All', 'value': 'All'}] + [{'label': state, 'value': state} for state in states]

#Define function to generate choropleth map
def generate_choropleth(dataframe, value_column, geojson):

    color_discrete_map = {
        '0-$0.4' : '#ffffe0',
        '$0.4-$1.0' : '#a5d5d8',
        '$1.0-$2.1' : '#73a2c6',
        '$2.1-$4.6' : '#4771b2',
        '$4.6-$695.0' : '#00429d'
    }

    fig = px.choropleth(
        dataframe,  # Use the passed DataFrame
        geojson=geojson,
        locations='FIPS',  # Ensure your FIPS column is named 'FIPS'
        color=value_column,
        color_discrete_map=color_discrete_map,
        featureidkey="properties.FIPS",
        scope="usa",
        labels={value_column: 'Donations per capita'}
    )
    fig.update_geos(fitbounds=None, visible=False)
    fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0},
                      mapbox_zoom=3
                      )
    return fig

#Define application layout
app.layout = html.Div([
    dcc.Store(id='stored-geojson', data=counties, storage_type='session'),
    dcc.Store(id='stored-data', data=df.to_dict('records'), storage_type='session'),
    dcc.Dropdown(
        id='state-dropdown',
        options=state_options,
        value="Alabama",
        placeholder='Select a state',
    ),
    dcc.Dropdown(
        id='party-dropdown',
        options=[
            {'label': 'Democratic Donations', 'value': 'DEM'},
            {'label': 'Republican Donations', 'value': 'REP'},
            {'label': 'Other Donations', 'value': 'OTHER'},
            {'label': 'Total Donations', 'value': 'TOTAL'}
        ],
        value='TOTAL'
    ),
    dcc.Graph(id='map-graph')
])

#Define app callback to handle two way communication
@app.callback(
    Output('map-graph', 'figure'),
    [Input('party-dropdown', 'value'), Input('state-dropdown', 'value')],
    [State('stored-data', 'data'), State('stored-geojson', 'data')]
)

#Define function to update the map based on user input
def update_map(selected_party, selected_state, stored_data, stored_geojson):
    filtered_df=pd.DataFrame(stored_data)
    geojson = stored_geojson
    #print(geojson)

    if selected_state == 'All':
        # If 'All' is selected, use the entire DataFrame
        pass
    else:
        # Filter the DataFrame for the selected state
        filtered_df = filtered_df[filtered_df['state'] == selected_state] if 'state' in filtered_df.columns else pd.DataFrame()

    # Generate the choropleth map using the filtered DataFrame and stored GeoJSON
    print(filtered_df.head())
    return generate_choropleth(filtered_df, selected_party, geojson)

# Run flask app
if __name__ == "__main__": app.run_server(debug=False, host='0.0.0.0', port=8050)

'''# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

# Define Dash layout
def create_dash_layout(app):

    # Set browser tab title
    app.title = "Your app title" 
    
    # Header
    header = html.Div([html.Br(), dcc.Markdown(""" # Hi. I'm your Dash app."""), html.Br()])
    
    # Body 
    body = html.Div([dcc.Markdown(""" ## I'm ready to serve static files on Heroku. Just look at this! """), html.Br(), html.Img(src='charlie.png')])

    # Footer
    footer = html.Div([html.Br(), html.Br(), dcc.Markdown(""" ### Built with ![Image](heart.png) in Python using [Dash](https://plotly.com/dash/)""")])
    
    # Assemble dash layout 
    app.layout = html.Div([header, body, footer])

    return app

# Construct the dash layout
create_dash_layout(app)
'''
