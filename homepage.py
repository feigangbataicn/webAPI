from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from app import app  # 从新的 app.py 导入 app 实例 # 导入中央 app 实例，以便注册回调
import data_handler

# ... 辅助函数，如 create_status_lights, create_machine_card ...
def create_status_lights(status_string):
    color_map = {'green': 'success', 'yellow': 'warning', 'red': 'danger'}
    active_light = color_map.get(status_string, "secondary")
    lights = []
    for color in ['success', 'warning', 'danger']:
        lights.append(
            dbc.Badge(" ", color=color if color == active_light else "secondary", 
                      className="me-1 rounded-pill", 
                      style={"width": "20px", "height": "20px", "opacity": 1.0 if color == active_light else 0.2})
        )
    return html.Div(lights)

def create_machine_card(machine_id, state_data):
    if 'error' in state_data:
        return dbc.Col(dbc.Card([dbc.CardHeader(f"设备: {machine_id}"), dbc.CardBody(dbc.Alert(state_data['error'], color="danger"))]), lg=4, md=6, sm=12)
    
    border_color_class = {'green': 'border-success', 'yellow': 'border-warning', 'red': 'border-danger'}.get(state_data.get('status_light'), 'border-secondary')
    card_body_content = [
        dbc.Row([
            dbc.Col("状态灯:", width=4, className="fw-bold"),
            dbc.Col(create_status_lights(state_data.get('status_light')), width=8),
        ], className="mb-2 align-items-center"),
        dbc.Row([
            dbc.Col("每小时进/出料:", width=6, className="fw-bold"),
            dbc.Col(f"{state_data.get('hourly_in', 'N/A')} / {state_data.get('hourly_out', 'N/A')}", width=6),
        ]),
        html.Hr(className="my-2"),
        dbc.Row([dbc.Col("入口状态:", width=6), dbc.Col(state_data.get('entrance_status', 'N/A'), width=6)]),
        dbc.Row([dbc.Col("处理状态:", width=6), dbc.Col(state_data.get('processing_status', 'N/A'), width=6)]),
        dbc.Row([dbc.Col("出口状态:", width=6), dbc.Col(state_data.get('exit_status', 'N/A'), width=6)]),
        dbc.Row([
            dbc.Col("错误代码:", width=6),
            dbc.Col(dbc.Badge(state_data.get('error_code', 'N/A'), color="danger" if str(state_data.get('error_code', '0')) != '0' else "secondary"), width=6),
        ]),
    ]
    card = dbc.Card([
        dbc.CardHeader(f"设备: {machine_id}", className="fw-bold"),
        dbc.CardBody(card_body_content)
    ], className=f"mb-4 shadow-sm {border_color_class} border-3")
    return dbc.Col(dcc.Link(href=f'/{machine_id}', children=card, style={'textDecoration': 'none', 'color': 'inherit'}), lg=4, md=6, sm=12)

# 定义主页的静态布局。这是 display_page 函数返回的内容。
# 它只包含一个标题、一个用于显示加载动画的容器，和一个定时器。
layout = dbc.Container([
    html.H1("设备总体情况看板", className="my-4 text-center"),
    dcc.Loading(id="loading-homepage-cards", type="default", children=dbc.Row(id='homepage-cards-container')),
    dcc.Interval(id='homepage-interval', interval=10 * 1000, n_intervals=0)
], fluid=True)

# 主页的核心回调函数
@app.callback(
    Output('homepage-cards-container', 'children'),
    Input('homepage-interval', 'n_intervals')
)
def update_homepage_cards(n):
    # 1. 调用 data_handler 获取所有设备ID    
    print(f"--- 主页更新回调函数已触发 (第 {n} 次) ---")
    machine_ids = data_handler.get_machine_list()
    print(f"找到的设备列表: {machine_ids}")
    if not machine_ids:
        return dbc.Alert("未找到任何设备数据。", color="danger")

    # 2. 循环遍历每个设备ID
    all_cards = [create_machine_card(mid, data_handler.get_latest_machine_state(mid)) for mid in machine_ids]
    # all_cards = []
    # for mid in machine_ids:
    #     # 3. 为每个设备调用 data_handler 获取其最新状态
    #     latest_state = data_handler.get_latest_machine_state(mid)
    #     # 4. 使用最新状态创建一个卡片组件
    #     card = create_machine_card(mid, latest_state)
    #     all_cards.append(card)    
    print(f"创建完成，共返回 {len(all_cards)} 个卡片。")
    
    # 5. 返回一个包含所有卡片组件的列表，Dash会自动更新前端页面    
    return all_cards