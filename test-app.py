# ----------------------------------
# 1. 导入所需库
# ----------------------------------
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import psutil
import datetime
import pandas as pd

# ----------------------------------
# 2. 初始化 Dash 应用
# ----------------------------------
# 使用 Bootstrap 的主题可以让界面更好看
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# 获取底层的 Flask server 实例，用于部署
server = app.server

# ----------------------------------
# 3. 定义应用布局 (Layout)
# ----------------------------------
app.layout = dbc.Container([
    # --- 标题行 ---
    dbc.Row([
        dbc.Col(html.H1("服务器设备信息监控面板", className="text-center text-primary, mb-4"), width=12)
    ]),

    # --- 实时指标卡片 ---
    dbc.Row([
        # CPU 使用率卡片
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("CPU 使用率"),
                dbc.CardBody([
                    dcc.Graph(id='cpu-gauge', config={'displayModeBar': False})
                ])
            ])
        ], width=6),

        # 内存使用率卡片
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("内存使用率"),
                dbc.CardBody([
                    dcc.Graph(id='memory-gauge', config={'displayModeBar': False})
                ])
            ])
        ], width=6),
    ], className="mb-4"),

    # --- 磁盘信息表格 ---
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("磁盘使用信息"),
                dbc.CardBody([
                    html.Div(id='disk-usage-table')
                ])
            ])
        ], width=12)
    ]),

    # --- 辅助组件 ---
    # 最后更新时间
    html.P(id='last-updated-time', className="text-muted text-center mt-4"),
    
    # 定时器组件：每5秒触发一次回调函数，更新数据
    dcc.Interval(
        id='interval-component',
        interval=5 * 1000,  # 5000毫秒 = 5秒
        n_intervals=0
    )
], fluid=True)


# ----------------------------------
# 4. 定义回调函数 (Callbacks)
#    这是 Dash 应用的核心，用于实现交互和数据更新
# ----------------------------------
@app.callback(
    [Output('cpu-gauge', 'figure'),
     Output('memory-gauge', 'figure'),
     Output('disk-usage-table', 'children'),
     Output('last-updated-time', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics(n):
    # --- a. 获取系统信息 ---
    cpu_percent = psutil.cpu_percent()
    mem_percent = psutil.virtual_memory().percent

    # 获取磁盘信息
    disk_partitions = psutil.disk_partitions()
    disk_data = []
    for partition in disk_partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_data.append({
                '设备': partition.device,
                '挂载点': partition.mountpoint,
                '总大小 (GB)': f"{usage.total / (1024**3):.2f}",
                '已用 (GB)': f"{usage.used / (1024**3):.2f}",
                '可用 (GB)': f"{usage.free / (1024**3):.2f}",
                '使用率 (%)': usage.percent
            })
        except PermissionError:
            # 忽略没有权限访问的驱动器 (例如 Windows 上的 CD-ROM)
            continue
    disk_df = pd.DataFrame(disk_data)

    # --- b. 创建图表和组件 ---
    
    # 创建 CPU 仪表盘
    cpu_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=cpu_percent,
        title={'text': "CPU %"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "dodgerblue"},
               'steps': [
                   {'range': [0, 50], 'color': "lightgreen"},
                   {'range': [50, 80], 'color': "yellow"},
                   {'range': [80, 100], 'color': "red"}],
               }))
    cpu_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))

    # 创建内存仪表盘
    memory_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mem_percent,
        title={'text': "内存 %"},
        gauge={'axis': {'range': [None, 100]},
               'bar': {'color': "dodgerblue"},
               'steps': [
                   {'range': [0, 50], 'color': "lightgreen"},
                   {'range': [50, 80], 'color': "yellow"},
                   {'range': [80, 100], 'color': "red"}],
               }))
    memory_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))

    # 创建磁盘信息表格
    disk_table = dbc.Table.from_dataframe(disk_df, striped=True, bordered=True, hover=True)
    
    # 更新时间戳
    update_time = f"最后更新于: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    # --- c. 返回所有更新后的组件 ---
    return cpu_gauge, memory_gauge, disk_table, update_time

# ----------------------------------
# 5. 启动应用
# ----------------------------------
if __name__ == '__main__':
    # debug=True 模式只在开发时使用，部署时必须关闭
    app.run(debug=True, host='0.0.0.0', port=8050)
# ```

# #### 步骤 4：本地运行和测试

# 在终端中，确保您位于 `app.py` 文件所在的目录，并且虚拟环境已激活，然后运行：
# ```bash
# python app.py
# ```
# 终端会显示类似下面的信息：
# ```
# Dash is running on http://0.0.0.0:8050/

#  * Serving Flask app 'app'
#  * Debug mode: on
# ```
# 现在，在您的浏览器中打开 `http://127.0.0.1:8050` 或 `http://localhost:8050`，您应该就能看到监控面板了。

# #### 步骤 5：服务器部署

# 当您准备好将网站部署到服务器上时，请**务必关闭 `debug=True` 模式**。然后使用 Gunicorn 启动应用。

# ```bash
# # -w 4 表示使用 4 个 worker 进程来处理请求，可以根据服务器CPU核心数调整
# # -b 0.0.0.0:8000 表示绑定到所有网络接口的 8000 端口
# # app:server 指的是 app.py 文件中的 server 对象
# gunicorn -w 4 -b 0.0.0.0:8000 app:server
# ```
# 现在，您就可以通过服务器的 IP 地址和 8000 端口（例如 `http://YOUR_SERVER_IP:8000`）来访问您的监控网站了。

# ---

# ### 最终效果展现

# 您的网站看起来会像下面这个示意图：

# ```
# +--------------------------------------------------------------------------+
# |                                                                          |
# |                   服务器设备信息监控面板                                 |
# |                                                                          |
# +------------------------------------------+-------------------------------+
# | |                 CPU 使用率               | |            内存使用率             | |
# | |                                          | |                                 | |
# | |              [  CPU 仪表盘  ]            | |           [ 内存仪表盘 ]            | |
# | |                                          | |                                 | |
# | |                                          | |                                 | |
# +------------------------------------------+-------------------------------+
# |                                                                          |
# +--------------------------------------------------------------------------+
# | |                            磁盘使用信息                                | |
# | |                                                                        | |
# | | [ 设备 | 挂载点 | 总大小 | 已用 | 可用 | 使用率 ]                    | |
# | | [ C:\  | C:\    | ...    | ...  | ...  | ...    ]                    | |
# | | [ D:\  | D:\    | ...    | ...  | ...  | ...    ]                    | |
# | |                                                                        | |
# +--------------------------------------------------------------------------+
# |                                                                          |
# |                      最后更新于: 2025-10-01 15:30:05                       |
# |                                                                          |
# +--------------------------------------------------------------------------+
