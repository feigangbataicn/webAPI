from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import configparser

# 从我们新的 app.py 文件中导入 app 实例
from app import app
# 导入服务器实例，以便部署时使用
from app import server 

# 导入每个页面的布局和回调逻辑
from pages import homepage, detail_page

# 定义应用的主布局
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# 页面导航的回调函数
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    # 这个函数是整个应用的“路由器”
    # Input 是 'url' 组件的 'pathname' 属性。当URL改变时，这个函数就会被触发。
    # pathname 参数会接收到当前的URL路径，例如 '/' 或 '/machine1'    
    if pathname == '/':
        # 如果是主页，就返回 homepage.py 中定义的 layout 变量        
        return homepage.layout
    elif pathname and pathname.startswith('/'):
        # 如果是详情页，就调用 detail_page.py 中的 create_layout 函数来生成布局        
        machine_id = pathname[1:]
        if 'machine' in machine_id:
             return detail_page.create_layout(machine_id)
    
    return html.Div(
        dbc.Container(
            [
                html.H1("404: Not found", className="display-3"),
                html.P(f"路径 {pathname} 未找到...", className="lead"),
                dbc.Button("返回主页", href="/", color="primary"),
            ],
            fluid=True, className="py-3",
        ),
        className="p-3 bg-light rounded-3",
    )

# 启动应用的入口
if __name__ == '__main__':
    # 读取配置文件来决定是否开启 debug 模式
    config = configparser.ConfigParser()
    # 【关键修改】: 添加 encoding='utf-8'
    config.read('config.ini', encoding='utf-8')
    is_debug_mode = (config.get('settings', 'environment', fallback='debug') == 'debug')
    
    # 只有在 debug 模式下才开启 debug=True
    app.run(debug=is_debug_mode, host='0.0.0.0', port=8050)