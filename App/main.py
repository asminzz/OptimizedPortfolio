import math
import plotly.express as px
from jupyter_dash import JupyterDash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash import dash_table, ctx
from dash.dependencies import Input, Output, State
import datafetcher
import pandas as pd
import numpy as np
import time

# Build App
app = JupyterDash(__name__, external_stylesheets=[dbc.themes.FLATLY])

days = 250
iterations = 1000
selected_companies = []
df_alldata = pd.DataFrame(datafetcher.getAllData())
df_companies = pd.DataFrame(datafetcher.getCompaniesListForTradedDays(days))
frontier_data = {}

app.layout = dbc.Container(
    [
        dbc.Row(dbc.Col(html.H2('PORTFOLIO OVERVIEW', className='text-center text-primary, mb-3'))),  # header row
        dbc.Row([  # start of second row
            dbc.Col([  # first column on second row -- stock selector
                html.H5('Add Company', className='text-center'),
                dash_table.DataTable(
                    id='datatable-interactivity',
                    columns=[
                        {"name": "Add Stocks", "id": i} for i in df_companies.columns
                    ],
                    data=df_companies.to_dict('records'),
                    # editable=True,
                    filter_action="native",
                    # sort_action="native",
                    # sort_mode="multi",
                    # column_selectable="single",
                    row_selectable="multi",
                    # row_deletable=True,
                    # selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current=0,
                    page_size=10,
                ),
                html.Hr(),
            ], width={'size': 2, 'offset': 0, 'order': 1}),  # width first column on second row
            dbc.Col([  # second column on second row -- selected stock display
                html.H5('Our Portfolio', className='text-center'),
                dash_table.DataTable(id='selections_table',
                                     columns=[
                                         {'id': i, 'name': "Stocks in Portfolio"} for i in df_companies.columns
                                     ],
                                     data=pd.DataFrame(selected_companies).to_dict('records'),
                                     # editable=True,
                                     # filter_action="native",
                                     # sort_action="native",
                                     # sort_mode="multi",
                                     # column_selectable="single",
                                     # row_selectable="multi",
                                     # row_deletable=True,
                                     # selected_columns=[],
                                     # selected_rows=[],
                                     page_action="native",
                                     page_current=0,
                                     page_size=10,
                                     ),
                html.Button('Calculate', id='btn-calc', n_clicks=0),
                html.Div(id='btn-text'),
            ], width={'size': 2, 'offset': 0, 'order': 2}),  # width second column on second row
            dbc.Col([  # third column on second row -- pie chart
                dcc.Graph(id="pie_chart",
                          style={'height': 550})
            ], width={'size': 4, 'offset': 0, 'order': 3}),  # width third column on second row
            dbc.Col([  # fourth column on second row
                dcc.Graph(id='chart_frontier',
                          # figure=chart_ptfvalue,
                            figure={
                              'layout': {
                                  'title': 'Efficient Frontier'
                              }
                            },
                          style={'height': 550},
                          ),
                html.Hr(),
            ], width={'size': 4, 'offset': 0, 'order': 4}),  # width third column on second row
        ]),  # end of second row
        dbc.Row([  # start of third row
            dbc.Col([  # first column on third row
                html.H5('Settings', id='header', className='text-center'),
                dcc.Input(
                            id="input_iterations",
                            type="number",
                            placeholder="Iterations (higher=slower calc)",
                        ),
                dcc.Input(
                            id="input_days",
                            type="number",
                            placeholder="No. of days (default 250)",
                        )
                # html.Label('', id='lbl_hidden'),
                # dcc.Graph(id='chrt-portfolio',
                #           # figure=fig_growth2,
                #           style={'height': 380}),
                ], width={'size': 2, 'offset': 0, 'order': 1}),  # width first column on second row
            dbc.Col([  # first column on third row
                dcc.Graph(id='chrt_portfolio_equal',
                          style={'height': 550}),
                html.Hr(),
            ], width={'size': 5, 'offset': 0, 'order': 1}),  # width first column on second row
            dbc.Col([  # second column on third row
                dcc.Graph(id='chrt_portfolio_optimum',
                          style={'height': 550}),
                html.Hr(),
            ], width={'size': 5, 'offset': 0, 'order': 2}),  # width second column on second row
        ])  # end of third row

    ], fluid=True)

# When iterdaysation settings is changed
@app.callback(
    Output("header", "children"),
    [Input("input_days", "value"),
     Input("input_iterations", "value")],
)
def cb_render(value_days, value_iterations):
    global iterations, days
    if type(value_days) == int:
        days= value_days
    else:
        days= 250

    if type(value_iterations) == int:
        iterations= value_iterations
    else:
        iterations= 1000
    print("iterations: "+str(iterations)+" days: "+str(days))
    return "Settings"

# When days settings is changed
# @app.callback(
#     Output("header", "children"),
#     [Input("input_days", "value")],
# )
# def cb_rendered(value):
#     global days
#     if type(value) == int:
#         days= value
#     else:
#         days= 250
#     return "Settings"

# When a row is selected or deleted
@app.callback(
    Output('selections_table', 'data'),
    [Input('datatable-interactivity', 'selected_rows')])
def update_tables(selected_rows):
    print("Fn update_tables")
    global selected_companies, frontier_data
    frontier_data = {}
    selected_companies = []
    for s in selected_rows:
        selected_companies.append(df_companies.iloc[s][0])

    print("Selected -> \t\t"+str(selected_companies))
    return pd.DataFrame(selected_companies).to_dict('records')

# When calculate button is clicked
@app.callback(
    [Output("chart_frontier", "figure"),
    Output("pie_chart", "figure"),
    Output("chrt_portfolio_equal", "figure"),
    Output("chrt_portfolio_optimum", "figure")],
    [Input('btn-calc', 'n_clicks')])
def calcClicked(n_clicks):
    print("Fn calcClicked")
    global selected_companies, frontier_data, days, iterations
    frontier_data = {}
    if n_clicks==0: # first load
        selected_companies=[]

    calculateEfficiency()

    vol_arr = frontier_data['vol_arr']
    ret_arr = frontier_data['ret_arr']
    sharpe_arr = frontier_data['sharpe_arr']
    all_weights = frontier_data['all_weights']
    max_sr_vol = vol_arr[sharpe_arr.argmax()]
    max_sr_ret = ret_arr[sharpe_arr.argmax()]

    print("max_sr_vol")
    print(max_sr_vol)
    figScatter1 = px.scatter(x= vol_arr, y= ret_arr, color= sharpe_arr, labels=dict(x="Volatility (Risk)", y="Sharpe Ratio (Return)"))\
        .add_scatter(x=[max_sr_vol], y=[max_sr_ret] )
    # figScatter2 = px.scatter(x=[max_sr_vol], y=[max_sr_ret])
    # figScatter = go.Figure(data=figScatter1.data + figScatter2.data)


    df = pd.DataFrame({"companies": selected_companies, "weight": all_weights[sharpe_arr.argmax()]})
    figPie = px.pie(df,  values='weight', names='companies', hole=.4, height=650)

    # For optimum distribution of companies
    nepseFrame = pd.DataFrame(datafetcher.getCompanyHistoricData('NEPSE'))
    xData = [time.strftime('%Y-%m-%d', time.localtime(item)) for item in nepseFrame.t.tail(days)]
    first_val = nepseFrame.c.tail(days).to_numpy()[0]
    weights = all_weights[sharpe_arr.argmax()]

    yDataOpt = np.zeros(shape=days)
    i = 0
    for com in selected_companies:
        comData = [item * weights[i] for item in datafetcher.getCompanyHistoricData(com)['c'][-1*days:]]
        yDataOpt += comData
        i=i+1

    yDataOpt = [item*(first_val/yDataOpt[0]) for item in yDataOpt]

    # For equal distribution of companies

    yDataEq = np.zeros(shape=days)
    i = 0
    for com in selected_companies:
        comData = [item * (1/len(selected_companies)) for item in datafetcher.getCompanyHistoricData(com)['c'][-1*days:]]
        yDataEq += comData
        i=i+1

    yDataEq = [item*(first_val/yDataEq[0]) for item in yDataEq]

    # Calculate range for y-axis:

    figEqual = {
          'data': [
              {'x': xData,
               'y': yDataEq,
               'type': 'line', 'name': 'Portfolio'}
              ,{'x': xData,
               'y': nepseFrame.c.tail(days),
               'type': 'line', 'name': 'NEPSE'}
          ],
          'layout': {
              'title': 'Equally Distributed Performance Return rate = '+str(math.trunc(((yDataEq[-1]-yDataEq[0])*100)/yDataEq[0]))+"%",
              'yaxis': {'range': [min(min(yDataOpt), min(yDataEq), min(nepseFrame.c.tail(days)))-150,
                                  max(max(yDataOpt), max(yDataEq), max(nepseFrame.c.tail(days)))+50]}
          }
    }
    figOptimum = {
        'data': [
            {'x': xData,
             'y': yDataOpt,
             'type': 'line', 'name': 'Portfolio'}
            , {'x': xData,
               'y': nepseFrame.c.tail(days),
               'type': 'line', 'name': 'NEPSE'}
        ],
        'layout': {
            'title': 'Optimally Distributed Performance Return rate = '+str(math.trunc(((yDataOpt[-1]-yDataOpt[0])*100)/yDataOpt[0]))+"%",
                      'yaxis': {'range': [min(min(yDataOpt), min(yDataEq), min(nepseFrame.c.tail(days)))-150,
                                          max(max(yDataOpt), max(yDataEq), max(nepseFrame.c.tail(days)))+50]}
        }
    }
    return figScatter1, figPie, figEqual, figOptimum


def calculateEfficiency():
    print("Fn calculateEfficiency")
    global selected_companies, frontier_data, days, iterations
    t = pd.Series(datafetcher.getCompanyHistoricData("NEPSE")["t"], name= "Date").tail(int(days))
    df = pd.DataFrame(index= t)
    print("Calculating efficiency for "+str(selected_companies))
    company_list = datafetcher.getCompaniesList()
    for company in selected_companies:
        if company in company_list:
            df[company] = (pd.Series(datafetcher.getCompanyHistoricData(company)["c"]).tail(int(days))).to_numpy()

    # print(df.head)
    frontier_data = datafetcher.getFrontierData(selected_companies, days, iterations)

# def getFrontier():
#     global selected_companies, frontier_data
#     if len(frontier_data.items())==0:
#         calculateEfficiency()
#     return frontier_data


# Run app and display result inline in the notebook
app.run_server(mode='inline')
