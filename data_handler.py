import pandas as pd
import numpy as np
import datetime
import os
import glob
import configparser

# --- 1. 读取配置文件 ---
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# --- 2. 根据配置决定数据目录和模式 ---
ENVIRONMENT = config.get('settings', 'environment', fallback='debug')

if ENVIRONMENT == 'production':
    BASE_DATA_DIR = config.get('paths', 'production_data_dir')
    print(f"--- 运行在生产模式 (Production Mode) ---")
    print(f"--- 数据源根目录: {BASE_DATA_DIR} ---")
else:
    local_data_folder = config.get('paths', 'debug_data_dir', fallback='machine_data')
    BASE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_data_folder)
    print(f"--- 运行在调试模式 (Debug Mode) ---")
    print(f"--- 数据源根目录: {BASE_DATA_DIR} ---")

# --- 3. 模拟数据生成函数 ---
def create_dummy_data(machine_id, days=30):
    # 只在调试模式下创建模拟数据，用于本地测试

    machine_path = os.path.join(BASE_DATA_DIR, machine_id, "csv")
    os.makedirs(machine_path, exist_ok=True)
    end_date = datetime.date.today()
    for i in range(days):
        current_date = end_date - datetime.timedelta(days=i)
        file_path = os.path.join(machine_path, f"state_{current_date.strftime('%y%m%d')}.txt")
        if os.path.exists(file_path): continue
        data = []
        start_time = datetime.datetime.combine(current_date, datetime.time(0, 0))
        for minute in range(24 * 60):
            ts = start_time + datetime.timedelta(minutes=minute)
            status_light = np.random.choice(['green', 'yellow', 'red'], p=[0.8, 0.15, 0.05])
            error_code = "E-" + str(np.random.randint(100, 105)) if status_light == 'red' else "0"
            data.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"), "in_count": np.random.randint(0, 5), "out_count": np.random.randint(0, 5),
                "status_light": status_light, "entrance_status": "ok" if status_light != 'red' else 'error',
                "processing_status": "running" if status_light == 'green' else 'idle', "exit_status": "ok", "error_code": error_code,
            })
        pd.DataFrame(data).to_csv(file_path, index=False)

# --- 4. 修改后的数据获取函数 ---
def get_machine_list():
    # 扫描 BASE_DATA_DIR 目录，返回所有设备文件夹的列表（['machine1', ...])
    # 如果是调试模式，会先调用 create_dummy_data 确保有数据可用

    try:
        if ENVIRONMENT == 'debug':
            os.makedirs(BASE_DATA_DIR, exist_ok=True)
            print("正在检查并生成模拟数据...")
            for mid in ["machine1", "machine2", "machine3"]: create_dummy_data(mid)
            print("模拟数据检查完毕。")
        if not os.path.exists(BASE_DATA_DIR):
            print(f"错误: 数据目录不存在: {BASE_DATA_DIR}")
            return []
        return [d for d in os.listdir(BASE_DATA_DIR) if os.path.isdir(os.path.join(BASE_DATA_DIR, d))]
    except (FileNotFoundError, OSError) as e:
        print(f"错误: 扫描数据目录 {BASE_DATA_DIR} 时出错: {e}")
        return []
    
def get_latest_machine_state(machine_id):
    # 根据传入的 machine_id，在对应的数据目录中找到最新的 state_*.txt 文件
    # 使用 pandas 读取文件，提取最后一行数据
    # 计算一些聚合值（如 hourly_in）
    # 以字典（dictionary）的形式返回最新状态    
    
    try:
        # 【关键改善】: 移除了只针对 'machine1' 的 if 判断，现在所有设备都使用这条统一的路径规则
        search_path = os.path.join(BASE_DATA_DIR, machine_id, "csv", "state_*.txt")
        
        print(f"正在搜索最新状态文件: {search_path}")

        list_of_files = glob.glob(search_path)
        if not list_of_files: 
            return {"error": f"在 {search_path} 中找不到数据文件"}
        
        latest_file = max(list_of_files, key=os.path.getctime)
        df = pd.read_csv(latest_file)
        latest_state = df.iloc[-1].to_dict()
        latest_state['hourly_in'] = df['in_count'].sum()
        latest_state['hourly_out'] = df['out_count'].sum()
        return latest_state
    except Exception as e:
        return {"error": f"读取最新状态时发生错误: {e}"}

def get_machine_production_data(machine_id, time_range_days):
    # 根据传入的 machine_id 和时间范围，找到所有相关的 state_*.txt 文件
    # 使用 pandas 逐个读取并合并它们
    # 以 DataFrame 的形式返回历史数据    
    
    try:
        all_data = []
        end_date = datetime.date.today()
        for i in range(time_range_days):
            current_date = end_date - datetime.timedelta(days=i)
            
            # 【关键改善】: 移除了只针对 'machine1' 的 if 判断，现在所有设备都使用这条统一的路径规则
            file_path = os.path.join(BASE_DATA_DIR, machine_id, "csv", f"state_{current_date.strftime('%y%m%d')}.txt")

            if os.path.exists(file_path): 
                all_data.append(pd.read_csv(file_path, parse_dates=['timestamp']))
        
        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
    except Exception as e:
        print(f"读取生产数据时出错: {e}")
        return pd.DataFrame()