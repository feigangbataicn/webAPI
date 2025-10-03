from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from app import app # 从新的 app.py 导入 app 实例
import data_handler

def create_layout(machine_id):
    """
    为指定设备ID动态创建布局
    这是一个函数而不是一个变量。
    当 index.py 的导航回调需要显示详情页时，它会调用此函数，并传入设备ID。
    这样我们就可以在页面标题等地方动态地显示设备ID。
    """    
    return dbc.Container([
        # 使用 dcc.Store 这个隐藏组件来“记住”当前页面的设备ID        
        dcc.Store(id='detail-page-machine-id', data=machine_id),
        dbc.Row([
            dbc.Col(html.H1(f"设备 {machine_id} 详细状态"), width=10),
            dbc.Col(dbc.Button("返回主页", href="/", color="secondary"), width=2, className="text-end"),
        ], align="center", className="my-4"),
        dbc.Card(id='detail-latest-status-card', className="mb-4"),
        dbc.Card([
            dbc.CardHeader("产量图"),
            dbc.CardBody([
                dbc.RadioItems(
                    id='time-range-selector',
                    options=[
                        {'label': '天', 'value': 1}, {'label': '周', 'value': 7}, {'label': '月', 'value': 30},
                    ],
                    value=1, inline=True, className="mb-3"
                ),
                dcc.Graph(id='production-chart')
            ])
        ]),
        dcc.Interval(id='detail-page-interval', interval=15 * 1000, n_intervals=0)
    ], fluid=True)

# 详情页的回调函数
@app.callback(
    Output('detail-latest-status-card', 'children'),
    Input('detail-page-interval', 'n_intervals'),
    State('detail-page-machine-id', 'data') # 使用 State 来获取设备ID
)
def update_detail_status_card(n, machine_id):

    state = data_handler.get_latest_machine_state(machine_id)
    if 'error' in state: return dbc.CardBody(dbc.Alert(state['error'], color="danger"))
    return dbc.CardBody([
        dbc.Row([
            dbc.Col(f"入口状态: {state.get('entrance_status', 'N/A')}", md=4),
            dbc.Col(f"处理状态: {state.get('processing_status', 'N/A')}", md=4),
            dbc.Col(f"出口状态: {state.get('exit_status', 'N/A')}", md=4),
        ]),
        html.Hr(),
        dbc.Row([
             dbc.Col(f"错误代码: {state.get('error_code', 'N/A')}", md=4),
             dbc.Col(f"当前时间: {state.get('timestamp', 'N/A')}", md=8),
        ])
    ])
    
@app.callback(
    Output('production-chart', 'figure'),
    [Input('detail-page-interval', 'n_intervals'), Input('time-range-selector', 'value')],
    [State('detail-page-machine-id', 'data')]
)
def update_production_chart(n, time_range_days, machine_id):
    # State 与 Input 的区别：
    # Input 的值改变会【触发】回调。
    # State 的值在回调被触发时【被读取】，但它的改变本身【不会触发】回调。
    # 这里我们用 State 获取 machine_id 是因为设备ID在页面加载后是固定的，我们只需要在更新时读取它即可。

    # 1. 根据 machine_id 和 time_range_days 调用 data_handler 获取历史数据    
    df = data_handler.get_machine_production_data(machine_id, time_range_days)
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title=f"在过去 {time_range_days} 天内找不到 {machine_id} 的生产数据", xaxis={"visible": False}, yaxis={"visible": False}, annotations=[{"text": "没有可显示的数据", "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 16}}])
        return fig
    df_hourly = df.set_index('timestamp').resample('h').agg({'in_count': 'sum', 'out_count': 'sum'}).reset_index()
    # 2. 使用 plotly.express (px) 创建图表对象
    fig = px.bar(df_hourly, x='timestamp', y=['in_count', 'out_count'], title=f'过去 {time_range_days} 天每小时进/出料数量', labels={'timestamp': '时间', 'value': '数量', 'variable': '类型'}, barmode='group')
    fig.update_layout(transition_duration=500)
    # 3. 返回图表对象，Dash会自动更新页面上的图表
    return fig