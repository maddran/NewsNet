import json
import pandas as pd
import tldextract
import networkx as nx
from collections import Counter
from datetime import datetime
import time

import matplotlib. pyplot as plt
import matplotlib
from matplotlib import cm
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

global G, G_FILTERED, FILTER

G = nx.DiGraph()
FILTER = 0

def getdatetime(datestring):
    return datetime.strptime(datestring, "%Y%m%d")

def getnetwork(summary, domains, from_date = None, to_date = None):
    global G

    # print(from_date, to_date)

    for source,d1 in summary.items():
        links = []
        article_count = 0
        for date, d2 in d1.items():
            if date == 'Unknown':
                continue
            if (from_date != None) and (getdatetime(date) < (from_date)):
                continue
            if ((to_date != None) and (getdatetime(date) > (to_date))):
                continue

            links.extend(d2['external_links'])
            linkcounts = Counter(links)
            article_count += d2['count']

        for dest,count in linkcounts.items():
            if (source in domains) and (dest in domains):
                G.add_edge(source, dest, count = count)
        
        nx.set_node_attributes(G,{source:article_count}, "count")

    for node in G.nodes(data = True):
        try:
            node[1]['count']
        except:
            nx.set_node_attributes(G,{node[0]:0}, "count")

    return G



def plot_network(G):

    latlon = list(zip(sources.Longitude, sources.Latitude))
    pos = dict(zip(sources.domain, latlon))

    lon = [pos[n][0] for n in G.nodes()]
    lat = [pos[n][1] for n in G.nodes()]

    node_deg = []
    node_col = []
    
    for node in G.nodes():
        in_edges = G.in_edges(node, data=True)
        out_edges = G.out_edges(node, data=True)

        in_deg = sum([i[2]['count'] for i in in_edges])
        out_deg = sum([i[2]['count'] for i in out_edges])

        node_deg.append(in_deg-out_deg)

    if len(node_deg) > 0:
        norm = matplotlib.colors.Normalize(vmin=min(node_deg), vmax=max(node_deg), clip=True)
        mapper = cm.ScalarMappable(norm=norm, cmap=cm.get_cmap('brg'))
        node_col = mapper.to_rgba(node_deg, bytes=True)
        node_col = [f"rgba({n[0]},{n[1]},{n[2]},0.8)" for n in node_col]


    node_sizes = [n[1]['count'] for n in G.nodes(data=True)]
    node_sizes = [(n*40/max(node_sizes))+10 for n in node_sizes]

    node_hoverinfo = [f"{n[0]}<br># articles = {n[1]['count']}" for n in G.nodes(data=True)]

    edge_widths = [G[u][v]['count'] for u,v in G.edges()]
    edge_widths = [(e*10/max(edge_widths))+1 for e in edge_widths]

    fig = go.Figure()

    fig.add_trace(go.Scattergeo(
        locationmode = 'ISO-3',
        lon = lon,
        lat = lat,
        hoverinfo = 'text',
        text = node_hoverinfo,
        mode = 'markers',
        marker = dict(
            size = node_sizes,
            color = node_col,
            line = dict(
                width = 0,
                color = 'rgba(68, 68, 68, 0.5)'
            )
        )))


    for i,(u,v,c) in enumerate(G.edges(data=True)):
        fig.add_trace(go.Scattergeo(
            lon = [pos[u][0], pos[v][0]],
            lat = [pos[u][1], pos[v][1]],
            hoverinfo = 'text',
            text = f"{u} TO {v}<br># links = {c['count']}",
            mode = 'lines',
            line = dict(
                width = edge_widths[i],
                color = 'rgba(20, 20, 20, 0.3)')
            ))


    fig.update_layout(
        showlegend = False,
        hovermode = 'closest',
        # autosize=True,
        # width=1500, 
        height=600,
        margin=dict( l=0, r=0, b=0, t=0, pad = 4, autoexpand=True ),
        geo = dict(
            scope = 'world',
            # projection_type = 'azimuthal equal area',
            showland = True,
            showcountries = True,
            showframe = False,
            landcolor = 'rgb(243, 243, 243)',
            countrycolor = 'rgb(204, 204, 204)',
        ),
    )

    return fig


with open("data/summary.json", 'r') as file:
    summary = json.load(file)

sources = pd.read_csv("sources.csv")
sources["domain"] = [tldextract.extract(url).domain for url in sources.URL]
domains = list(set(sources['domain']))

min_date = datetime(2020, 5, 1)
max_date = datetime(2020, 6, 30)

G = getnetwork(summary, domains)
fig = plot_network(G)

nameLU = dict(zip(sources['domain'], sources['Name']))
dd_nodes = [{"label": "All", "value":"all"}]+[{"label": nameLU[n], "value":n} for n in sorted(G.nodes())]

daterange = pd.date_range(start=min_date,end=max_date,freq='d')

def unixTimeMillis(dt):
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(dt.timetuple()))

def unixToDatetime(unix):
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix,unit='s')

def getMarks(start, end, Nth=6):
    ''' Returns the marks for labeling. 
        Every Nth value will be used.
    '''
    result = {}
    for i, date in enumerate(daterange):
        if(date.is_month_start or date.day==15 or i == len(daterange)-1):
            # Append value to dict
            result[unixTimeMillis(date)] = str(date.strftime('%b %d'))

    return result

controls = dbc.Card([
                dbc.FormGroup([
                    dbc.Label("Select Date Range:"),
                    dcc.RangeSlider(
                        id='date_slider',
                        min = unixTimeMillis(daterange.min()),
                        max = unixTimeMillis(daterange.max()),
                        value = [unixTimeMillis(daterange.min()),
                                unixTimeMillis(daterange.max())],
                        marks=getMarks(daterange.min(),
                                    daterange.max())
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Filter only links FROM:"),
                    dcc.Dropdown(
                        id = "from-dd",
                        options= dd_nodes,
                        multi=False,
                        value = "all"
                    )
                ]),
                dbc.FormGroup([
                    dbc.Label("Filter only links TO:"),
                    dcc.Dropdown(
                        id = "to-dd",
                        options= dd_nodes,
                        multi=False,
                        value = "all"
                    )
                ])
            ], body = True)

header = dbc.Jumbotron(dbc.Container([
            html.H1("The Global News Network", className="display-3"),
            html.P(
                "Visualizing links between global news sources.",
                className="lead",
            )], fluid=True)
        )

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container([
                header,
                dbc.Row([
                        #controls
                        dbc.Col(controls, md=3),

                        #graph
                        dbc.Col(
                            dcc.Graph(figure=fig, 
                                      id = "map",
                                      config={
                                        'displayModeBar': True
                                        }), md=9
                            ),
                    ], align = "start", justify = "start")
                ], 
            fluid=True)


@app.callback(
    Output('map', 'figure'),
    [Input('to-dd', 'value'),
    Input('from-dd', 'value'),
    Input('date_slider', 'value')])
def update_map(value_to, value_from, date_range):
    global G, G_FILTERED, FILTER

    # G_FILTERED = G.copy()

    start_date = unixToDatetime(date_range[0])
    end_date = unixToDatetime(date_range[1])

    G_FILTERED = getnetwork(summary, domains, start_date, end_date)
    fig_update = plot_network(G_FILTERED)
    FILTER = 1


    if value_from != "all":
        out_edges = G_FILTERED.out_edges(value_from, data=False)
        G_FILTERED = G_FILTERED.edge_subgraph(out_edges).copy()
        FILTER = 1

    if value_to != "all":
        in_edges = G_FILTERED.in_edges(value_to, data=False)
        G_FILTERED = G_FILTERED.edge_subgraph(in_edges).copy()
        FILTER = 1

    fig_update = plot_network(G_FILTERED)
    return fig_update




if __name__ == "__main__":




    app.run_server(debug=False, use_reloader=False)

