import dash
import dash_bootstrap_components as dbc

# 这两行是核心：
# 1. 创建一个全局的、唯一的 Dash 应用实例，命名为 app
# 2. 所有其他的模块都会从这个文件导入这同一个 app 实例
# 这个文件只做一件事：创建 Dash app 实例，以便其他文件可以从中导入。
# 我们不再在这里定义布局或回调。
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server