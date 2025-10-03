import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import datetime
import os
import glob
import plotly.express as px

# --- 1. 初始化 Dash 应用 ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# --- 2. 数据处理逻辑 (从 data_handler.py 移入) ---
BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "machine_data")

def create_dummy_data(machine_id, days=1): # 只生成1天的数据以加快启动速度
    machine_path = os.path.join(BASE_DATA_DIR, machine_id, "csv")
    os.makedirs(machine_path, exist_ok=True)
    date_str = datetime.date.today().strftime("%y%m%d")
    file_path = os.path.join(machine_path, f"state_{date_str}.txt")
    if os.path.exists(file_path): return

    data = [{"timestamp": (datetime.datetime.combine(datetime.date.today(), datetime.time(0,0)) + datetime.timedelta(minutes=m)).strftime("%Y-%m-%d %H:%M:%S"), "in_count": np.random.randint(0,5), "out_count": np.random.randint(0,5), "status_light": np.random.choice(['green', 'yellow', 'red'], p=[0.8,0.15,0.05])} for m in range(24*60)]
    for row in data: row.update({"error_code": "E-101" if row['status_light']=='red' else "0", "entrance_status": "ok", "processing_status":"running", "exit_status":"ok"})
    pd.DataFrame(data).to_csv(file_path, index=False)

def get_machine_list():
    try:
        os.makedirs(BASE_DATA_DIR, exist_ok=True)
        print("正在检查并生成模拟数据...")
        for mid in ["machine1", "machine2", "machine3"]: create_dummy_data(mid)
        print("模拟数据检查完毕。")
        return [d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(os.path.join(BASE_DATA_DIR, d))]
    except Exception as e:
        print(f"错误: 扫描数据目录时出错: {e}")
        return []

def get_latest_machine_state(machine_id):
    try:
        search_path = os.path.join(BASE_DATA_DIR, machine_id, "csv", "state_*.txt")
        latest_file = max(glob.glob(search_path), key=os.path.getctime)
        df = pd.read_csv(latest_file)
        latest_state = df.iloc[-1].to_dict()
        latest_state['hourly_in'] = df['in_count'].sum()
        latest_state['hourly_out'] = df['out_count'].sum()
        return latest_state
    except Exception as e:
        return {"error": str(e)}

# --- 3. 主页布局和回调 (从 homepage.py 移入) ---
def create_status_lights(status_string):
    color_map = {'green': 'success', 'yellow': 'warning', 'red': 'danger'}
    active_light = color_map.get(status_string, "secondary")
    lights = [dbc.Badge(" ", color=active_light if c == active_light else "secondary", className="me-1 rounded-pill", style={"width": "20px", "height": "20px", "opacity": 1.0 if c == active_light else 0.3}) for c in ['success', 'warning', 'danger']]
    return html.Div(lights)

def create_machine_card(machine_id, state_data):
    if 'error' in state_data:
        return dbc.Col(dbc.Card([dbc.CardHeader(f"设备: {machine_id}"), dbc.CardBody(dbc.Alert(state_data['error'], color="danger"))]), lg=4, md=6, sm=12)
    border_color_class = {'green': 'border-success', 'yellow': 'border-warning', 'red': 'border-danger'}.get(state_data.get('status_light'), 'border-secondary')
    card_body_content = [
        dbc.Row([dbc.Col("状态灯:", width=4, className="fw-bold"), dbc.Col(create_status_lights(state_data.get('status_light')), width=8)], className="mb-2 align-items-center"),
        dbc.Row([dbc.Col("每小时进/出料:", width=6, className="fw-bold"), dbc.Col(f"{state_data.get('hourly_in', 'N/A')} / {state_data.get('hourly_out', 'N/A')}", width=6)]),
        html.Hr(className="my-2"),
        dbc.Row([dbc.Col("错误代码:", width=6), dbc.Col(dbc.Badge(state_data.get('error_code', 'N/A'), color="danger" if str(state_data.get('error_code', '0')) != '0' else "secondary"), width=6)]),
    ]
    card = dbc.Card([dbc.CardHeader(f"设备: {machine_id}", className="fw-bold"), dbc.CardBody(card_body_content)], className=f"mb-4 shadow-sm {border_color_class} border-3")
    return dbc.Col(dcc.Link(href=f'/{machine_id}', children=card, style={'textDecoration': 'none', 'color': 'inherit'}), lg=4, md=6, sm=12)

app.layout = dbc.Container([
    html.H1("设备总体情况看板 (单文件测试版)", className="my-4 text-center"),
    dcc.Loading(id="loading-homepage-cards", type="default", children=dbc.Row(id='homepage-cards-container')),
    dcc.Interval(id='homepage-interval', interval=10 * 1000, n_intervals=0)
], fluid=True)

@app.callback(
    Output('homepage-cards-container', 'children'),
    Input('homepage-interval', 'n_intervals')
)
def update_homepage_cards(n):
    print(f"--- 单文件版回调函数已触发 (第 {n} 次) ---")
    machine_ids = get_machine_list()
    print(f"找到的设备列表: {machine_ids}")
    if not machine_ids:
        return dbc.Alert("未找到任何设备数据。", color="danger")
    all_cards = [create_machine_card(mid, get_latest_machine_state(mid)) for mid in machine_ids]
    print(f"创建完成，共返回 {len(all_cards)} 个卡片。")
    return all_cards

# --- 4. 启动应用 ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8060)