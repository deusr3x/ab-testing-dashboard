import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash
from dash.dependencies import Input, Output, State
import scipy.stats as scs
from scipy.stats import beta
from scipy.stats import gamma
import numpy as np
import plotly.graph_objects as go


def calc_hdi(arr, hdi_prob=0.94):
    arr = arr.flatten()
    n = len(arr)
    arr = np.sort(arr)
    interval_idx_inc = int(np.floor(hdi_prob * n))
    n_intervals = n - interval_idx_inc
    interval_width = arr[interval_idx_inc:] - arr[:n_intervals]
    min_idx = np.argmin(interval_width)
    hdi_min = arr[min_idx]
    hdi_max = arr[min_idx + interval_idx_inc]
    hdi_interval = np.array([hdi_min, hdi_max])
    return hdi_interval


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server
SIM_SAMPLE = 10000
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "20rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

CONTENT_STYLE = {
    "margin-left": "26rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

parameter_input = dbc.FormGroup(
    [
        dbc.Label("Enter Number of Users for A:", html_for="users-a"),
        dbc.Input(type="number", id="users-a", value=1500),
        dbc.Label("Enter Number of Conversions for A:", html_for="conv-a"),
        dbc.Input(type="number", id="conv-a", value=10),
        dbc.Label("Enter Number of Users for B:", html_for="users-b"),
        dbc.Input(type="number", id="users-b", value=1500),
        dbc.Label("Enter Number of Conversions for B:", html_for="conv-b"),
        dbc.Input(type="number", id="conv-b", value=20),
    ]
)
form = dbc.Form([parameter_input])
sidebar = html.Div(
    [
        html.H4("Parameters", className="display-6"),
        html.Hr(),
        html.P(
            "Enter required parameters", className="lead"
        ),
        form,
        dbc.Button("Calculate", id="calc-num", className="mr-1"),
    ],
    style=SIDEBAR_STYLE,
)

plot1 = html.Div(
    dcc.Graph(
        id="plot-1",
        config={'displayModeBar': False}
    )
)
plot2 = html.Div(
    dcc.Graph(
        id="plot-2",
        config={'displayModeBar': False}
    )
)
plot3 = html.Div(
    dcc.Graph(
        id="plot-3",
        config={'displayModeBar': False}
    )
)
plot4 = html.Div(
    dcc.Graph(
        id="plot-4",
        config={'displayModeBar': False}
    )
)
listgroup = html.Div(
    [
        html.Br(),
        html.Br(),
        html.Div(
            id='list-data'
        )
    ]
)
content = html.Div(
    [
        html.H6("A/B Testing Tools", className="display-4"),
        html.Hr(),
        html.Div([
            dbc.Row(
                [
                    dbc.Col(plot1, width=4),
                    dbc.Col(plot2, width=4),
                    dbc.Col(plot3, width=4),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(plot4, width=6),
                    dbc.Col(listgroup, width="auto"),
                ]
            )
        ]),
    ],
    id="page-content",
    style=CONTENT_STYLE,
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Bayesian Results</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])


@app.callback(
    [
        Output("plot-1", "figure"),
        Output("plot-2", "figure"),
        Output("plot-3", "figure"),
        Output("plot-4", "figure"),
        Output("list-data", "children"),
    ],
    [
        Input("calc-num", "n_clicks"),
        State("users-a", "value"),
        State("conv-a", "value"),
        State("users-b", "value"),
        State("conv-b", "value"),
    ]
)
def calc(n, total_a=1500, conversions_a=10, total_b=1500, conversions_b=20):
    alpha_A = conversions_a + 1
    alpha_B = conversions_b + 1
    beta_A = total_a - conversions_a + 1
    beta_B = total_b - conversions_b + 1
    lambdaA = beta(alpha_A, beta_A).rvs(SIM_SAMPLE)
    lambdaB = beta(alpha_B, beta_B).rvs(SIM_SAMPLE)
    fig = go.Figure()
    xvarA = lambdaA
    xvarB = lambdaB
    fig.add_trace(go.Histogram(x=xvarA, name=f'Variant A', marker_color='#25211f'))
    fig.add_trace(go.Histogram(x=xvarB, name=f'Variant B', marker_color='#b51e6d'))
    fig.update_layout(
        barmode='overlay',
        title_text='Average Conversion Rate'
    )
    fig.update_traces(opacity=0.75)
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(x=xvarB - xvarA, name='B - A', marker_color='#b51e6d'))
    hdi = calc_hdi(xvarB - xvarA)
    fig2.update_layout(
        title_text=f'Conversion Rate Difference Between A and B',
        shapes=[
            dict(
                type='line',
                yref='paper',
                y0=0, y1=1,
                xref='x', x0=0, x1=0,
                line=dict(
                    dash='dashdot'
                )
            ),
            dict(
                type='line',
                xref='x', x0=hdi[0], x1=hdi[1],
                yref='y', y0=10, y1=10,
                line=dict(
                    width=5
                )
            )
        ]
    )
    fig2.update_traces(opacity=0.75)
    convProbBbeatsA = (lambdaB > lambdaA).mean()
    convProbAbeatsB = 1 - convProbBbeatsA
    colours = ['#25211f', '#b51e6d']
    fig3 = go.Figure([go.Bar(y=['Prob B beats A', 'Prob A beats B'], x=[convProbBbeatsA*100, convProbAbeatsB*100], marker_color=colours, orientation='h')])
    fig3.update_traces(opacity=0.75)
    fig3.update_layout(title_text="Win Probability")

    crA = conversions_a / total_a
    crB = conversions_b / total_b
    uplift = (crB - crA) / crA
    # crA_temp = crA
    # crB_temp = crB
    # total_a_temp = total_a
    # total_b_temp = total_b
    # if crA > crB:
    #     crA = crB_temp
    #     crB = crA_temp
    #     total_a = total_b_temp
    #     total_b = total_a_temp
    var_A = crA*(1 - crA)
    var_B = crB*(1 - crB)
    # sigA = np.sqrt(var_A)
    # sigB = np.sqrt(var_B)
    Z = (crB - crA) / np.sqrt(var_B/total_b + var_A/total_a)
    Z_alpha = scs.norm(0, 1).ppf(1 - 0.05/2)

    pval = scs.norm.sf(Z)
    if pval > 0.5:
        pval = 1 - pval
    StE_A = np.sqrt(crA*(1 - crA) / total_a)
    StE_B = np.sqrt(crB*(1 - crB) / total_b)
    
    lower = crA - Z_alpha * StE_A
    upper = crA + Z_alpha * StE_A
    
    lower_a = scs.norm.cdf(lower, crB, StE_B)
    upper_a = 1 - scs.norm.cdf(upper, crB, StE_B)
    
    power = round(100*(lower_a+upper_a), 2)
    x = np.linspace(0, crA + crB*1.5, 1000)
    normA = scs.norm.pdf(x, loc=crA, scale=StE_A)
    normB = scs.norm.pdf(x, loc=crB, scale=StE_B)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=x, y=normA, mode='lines', marker_color="#25211f", name='Dist A'))
    fig4.add_trace(go.Scatter(x=x, y=normB, mode='lines', marker_color="#b51e6d", name='Dist B'))
    fig4.add_vline(x=upper, line_width=3, line_dash="dash", line_color="green", annotation_text="95%")
    fig4.add_vline(x=lower, line_width=3, line_dash="dash", line_color="green", annotation_text="95%")
    fig4.update_layout(title_text="Expected Distributions")
    listg = dbc.ListGroup(
        [
            dbc.ListGroupItem(f"p value: {pval:0.4f}"),
            dbc.ListGroupItem(f"Power: {power}%"),
            dbc.ListGroupItem(f"Conversion Rate A: {100*crA:0.2f}%"),
            dbc.ListGroupItem(f"Conversion Rate B: {100*crB:0.2f}%"),
            dbc.ListGroupItem(f"Z: {Z:0.2f}"),
            dbc.ListGroupItem(f"lower_a: {lower_a:0.2f}"),
            dbc.ListGroupItem(f"upper_a: {upper_a:0.2f}"),
        ]
    )
    return fig, fig2, fig3, fig4, listg


if __name__ == '__main__':
    print('webserver starting on localhost:8050')
    app.run_server(debug=True, host='0.0.0.0', port=8050)
