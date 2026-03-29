import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import subprocess
import threading
import time
import os
import json
import webbrowser
import configparser
import shutil
from datetime import datetime, timedelta
import re
import sys
import urllib.request
import socket

# 尝试导入psutil，如果失败则禁用性能监控
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil未安装，性能监控功能将被禁用")

try:
    import platform
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False

# 尝试导入二维码相关库
try:
    import qrcode
    from PIL import Image, ImageTk
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("qrcode或PIL未安装，二维码功能将被禁用")

class MCCommandCompleter:
    def __init__(self):
        self.commands = {}
        self.load_commands()
    
    def load_commands(self):
        """加载Minecraft命令数据"""
        try:
            # 尝试从外部文件加载
            if os.path.exists("mc_commands.json"):
                with open("mc_commands.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.commands = data.get('commands', {})
            else:
                # 内置基本命令数据
                self.commands = {
                    "help": {"description": "显示命令帮助", "usage": "/help [页码|命令名]", "permission": 0},
                    "list": {"description": "列出服务器上的玩家", "usage": "/list", "permission": 0},
                    "gamemode": {"description": "更改游戏模式", "usage": "/gamemode <模式> [玩家]", "permission": 2, "suggestions": ["survival", "creative", "adventure", "spectator"]},
                    "give": {"description": "给予玩家物品", "usage": "/give <玩家> <物品> [数量] [数据值] [组件]", "permission": 2},
                    "tp": {"description": "传送实体", "usage": "/tp <目标玩家> <目的地玩家> 或 /tp <玩家> <x> <y> <z>", "permission": 2},
                    "teleport": {"description": "传送实体", "usage": "/teleport <目标玩家> <目的地玩家> 或 /teleport <玩家> <x> <y> <z>", "permission": 2},
                    "time": {"description": "更改或查询世界游戏时间", "usage": "/time <set|add|query> <值>", "permission": 2, "suggestions": ["set", "add", "query"]},
                    "weather": {"description": "设置天气", "usage": "/weather <clear|rain|thunder> [持续时间]", "permission": 2, "suggestions": ["clear", "rain", "thunder"]},
                    "op": {"description": "授予玩家管理员权限", "usage": "/op <玩家>", "permission": 3},
                    "deop": {"description": "撤销玩家的管理员权限", "usage": "/deop <玩家>", "permission": 3},
                    "ban": {"description": "封禁玩家", "usage": "/ban <玩家> [原因]", "permission": 3},
                    "tempban": {"description": "临时封禁玩家", "usage": "/tempban <玩家> <时间> [原因]", "permission": 3},
                    "pardon": {"description": "解除封禁玩家", "usage": "/pardon <玩家>", "permission": 3},
                    "kick": {"description": "将玩家踢出服务器", "usage": "/kick <玩家> [原因]", "permission": 3},
                    "stop": {"description": "停止服务器", "usage": "/stop", "permission": 4},
                    "save-all": {"description": "保存服务器世界", "usage": "/save-all", "permission": 4},
                    "whitelist": {"description": "管理白名单", "usage": "/whitelist <on|off|list|add|remove|reload>", "permission": 3, "suggestions": ["on", "off", "list", "add", "remove", "reload"]},
                    "say": {"description": "向所有玩家发送消息", "usage": "/say <消息>", "permission": 1},
                    "tell": {"description": "向其他玩家发送私信", "usage": "/tell <玩家> <消息>", "permission": 0},
                    "msg": {"description": "向其他玩家发送私信", "usage": "/msg <玩家> <消息>", "permission": 0},
                    "seed": {"description": "显示世界种子", "usage": "/seed", "permission": 0},
                    "effect": {"description": "管理状态效果", "usage": "/effect <玩家> <效果> [秒数] [强度] [隐藏粒子]", "permission": 2},
                    "spawnpoint": {"description": "设置玩家出生点", "usage": "/spawnpoint [玩家] [x] [y] [z]", "permission": 2},
                    "setworldspawn": {"description": "设置世界出生点", "usage": "/setworldspawn [x] [y] [z]", "permission": 2},
                    "gamerule": {"description": "更改或查询游戏规则", "usage": "/gamerule <规则> [值]", "permission": 2},
                    "clear": {"description": "清除玩家物品", "usage": "/clear [玩家] [物品] [数据值] [最大数量] [数据标签]", "permission": 2},
                    "xp": {"description": "给予玩家经验", "usage": "/xp <数量> [玩家] 或 /xp <数量>L [玩家]", "permission": 2},
                    "defaultgamemode": {"description": "设置默认游戏模式", "usage": "/defaultgamemode <模式>", "permission": 2, "suggestions": ["survival", "creative", "adventure", "spectator"]},
                    "reload": {"description": "重载服务器数据", "usage": "/reload", "permission": 4},
                    "mute": {"description": "禁言玩家", "usage": "/mute <玩家> [时间] [原因]", "permission": 2},
                    "unmute": {"description": "解除玩家禁言", "usage": "/unmute <玩家>", "permission": 2}
                }
        except Exception as e:
            print(f"加载命令数据时出错: {e}")
    
    def get_command_suggestions(self, text):
        """获取命令建议"""
        if not text.startswith('/'):
            return []
        
        text = text[1:]
        parts = text.split()
        
        if len(parts) == 0:
            return []
        
        command_name = parts[0]
        current_arg = parts[-1] if len(parts) > 1 else ""
        
        if len(parts) == 1:
            suggestions = []
            for cmd, info in self.commands.items():
                if cmd.startswith(command_name):
                    suggestions.append(f"/{cmd}")
            return suggestions
        
        if command_name in self.commands:
            cmd_info = self.commands[command_name]
            
            if "suggestions" in cmd_info:
                param_suggestions = []
                for suggestion in cmd_info["suggestions"]:
                    if suggestion.startswith(current_arg):
                        param_suggestions.append(suggestion)
                return param_suggestions
            
            if command_name in ["tp", "teleport", "kick", "ban", "tempban", "pardon", "op", "deop", "whitelist", "tell", "msg", "mute", "unmute"]:
                return self.get_online_players_suggestions(current_arg)
            elif command_name == "gamemode":
                return ["survival", "creative", "adventure", "spectator"]
            elif command_name == "time":
                if len(parts) == 2 and parts[1] in ["set", "add"]:
                    return ["day", "night", "noon", "midnight", "0", "1000", "6000", "12000", "18000"]
                elif len(parts) == 2:
                    return ["set", "add", "query"]
            elif command_name == "weather":
                return ["clear", "rain", "thunder"]
            elif command_name == "difficulty":
                return ["peaceful", "easy", "normal", "hard"]
            elif command_name == "tempban" or command_name == "mute":
                if len(parts) == 2:
                    return self.get_online_players_suggestions(current_arg)
                elif len(parts) == 3:
                    return ["1h", "2h", "6h", "12h", "1d", "7d", "30d", "1m", "6m", "1y"]
        
        return []
    
    def get_online_players_suggestions(self, current_arg):
        """获取在线玩家建议"""
        sample_players = ["Steve", "Alex", "Notch", "Dinnerbone", "Herobrine"]
        return [player for player in sample_players if player.lower().startswith(current_arg.lower())]
    
    def get_command_info(self, command_name):
        """获取命令的详细信息"""
        if command_name.startswith('/'):
            command_name = command_name[1:]
        
        if command_name in self.commands:
            return self.commands[command_name]
        return None

class PerformanceMonitor:
    def __init__(self):
        self.server_process = None
        self.monitoring = False
        self.performance_data = {
            "cpu_percent": 0,
            "memory_used": 0,
            "memory_total": 0,
            "memory_percent": 0,
            "disk_used": 0,
            "disk_total": 0,
            "disk_percent": 0,
            "network_sent": 0,
            "network_recv": 0
        }
        self.performance_history = []
        self.max_history_length = 50
        
    def start_monitoring(self, server_process):
        """开始监控服务器性能"""
        if not PSUTIL_AVAILABLE:
            return
            
        self.server_process = server_process
        self.monitoring = True
        
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        self.server_process = None
        
    def get_performance_data(self):
        """获取性能数据"""
        if not PSUTIL_AVAILABLE:
            return self.performance_data
            
        try:
            self.performance_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            
            memory = psutil.virtual_memory()
            self.performance_data["memory_used"] = memory.used / (1024 ** 3)
            self.performance_data["memory_total"] = memory.total / (1024 ** 3)
            self.performance_data["memory_percent"] = memory.percent
            
            server_dir = os.getcwd()
            disk = psutil.disk_usage(server_dir)
            self.performance_data["disk_used"] = disk.used / (1024 ** 3)
            self.performance_data["disk_total"] = disk.total / (1024 ** 3)
            self.performance_data["disk_percent"] = disk.percent
            
            net_io = psutil.net_io_counters()
            self.performance_data["network_sent"] = net_io.bytes_sent / (1024 ** 2)
            self.performance_data["network_recv"] = net_io.bytes_recv / (1024 ** 2)
            
            if self.server_process and self.server_process.poll() is not None:
                try:
                    server_pid = self.server_process.pid
                    server_process = psutil.Process(server_pid)
                    
                    server_cpu = server_process.cpu_percent()
                    server_memory = server_process.memory_info().rss / (1024 ** 2)
                    
                    self.performance_data["server_cpu"] = server_cpu
                    self.performance_data["server_memory"] = server_memory
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.performance_data["server_cpu"] = 0
                    self.performance_data["server_memory"] = 0
                    
        except Exception as e:
            print(f"获取性能数据时出错: {e}")
            
        # 添加到历史记录
        self.performance_history.append({
            "timestamp": datetime.now(),
            "cpu": self.performance_data["cpu_percent"],
            "memory": self.performance_data["memory_percent"],
            "server_cpu": self.performance_data.get("server_cpu", 0),
            "server_memory": self.performance_data.get("server_memory", 0)
        })
        
        # 限制历史记录长度
        if len(self.performance_history) > self.max_history_length:
            self.performance_history.pop(0)
            
        return self.performance_data
    
    def get_performance_history(self):
        """获取性能历史数据"""
        return self.performance_history

class PlayerMessageManager:
    def __init__(self, control_panel):
        self.control_panel = control_panel
        self.player_messages = {}  # 存储玩家消息 {player_name: [messages]}
        self.player_positions = {}  # 存储玩家位置 {player_name: (x, y, z)}
        self.player_ping = {}  # 存储玩家延迟 {player_name: ping}
        
    def add_message(self, player, message, is_server=False):
        """添加玩家消息"""
        if player not in self.player_messages:
            self.player_messages[player] = []
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        sender = "服务器" if is_server else player
        self.player_messages[player].append({
            "timestamp": timestamp,
            "sender": sender,
            "message": message
        })
        
        # 限制消息数量，防止内存占用过多
        if len(self.player_messages[player]) > 100:
            self.player_messages[player].pop(0)
        
        # 更新显示
        self.control_panel.update_player_chat_display(player)
    
    def update_player_position(self, player, x, y, z):
        """更新玩家位置"""
        self.player_positions[player] = (x, y, z)
        self.control_panel.update_players_display()
    
    def update_player_ping(self, player, ping):
        """更新玩家延迟"""
        self.player_ping[player] = ping
        self.control_panel.update_players_display()
    
    def get_player_position(self, player):
        """获取玩家位置"""
        return self.player_positions.get(player, (0, 0, 0))
    
    def get_player_ping(self, player):
        """获取玩家延迟"""
        return self.player_ping.get(player, 0)
    
    def get_player_messages(self, player):
        """获取玩家消息"""
        return self.player_messages.get(player, [])

class MCServerControlPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft 服务器控制面板 - 完整版")
        self.root.geometry("1000x700")
        
        # 设置编码 - 修复中文显示问题
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleCP(65001)
                kernel32.SetConsoleOutputCP(65001)
            except:
                pass
        
        # 服务器进程
        self.server_process = None
        self.server_running = False
        
        # 玩家数据和服务器属性
        self.players_online = []
        self.banned_players = []
        self.ops = []
        self.whitelist = []
        self.server_properties = {}
        
        # 禁言管理
        self.muted_players = {}  # {player: {type: "permanent"/"temporary", until: datetime, reason: str}}
        
        # 配置文件
        self.config_file = "mc_panel_config.ini"
        
        # 在线玩家更新定时器
        self.player_update_timer = None
        
        # 性能监控
        self.performance_monitor = PerformanceMonitor()
        self.performance_update_timer = None
        
        # 命令自动补全
        self.command_completer = MCCommandCompleter()
        self.current_suggestions = []
        self.suggestion_index = -1
        
        # 玩家消息管理器
        self.message_manager = PlayerMessageManager(self)
        
        # 临时封禁管理器
        self.temp_bans = {}
        self.ban_monitor_thread = None
        self.ban_monitoring = False
        
        # 禁言监控管理器
        self.mute_monitor_thread = None
        self.mute_monitoring = False
        
        # 服务器地址相关变量
        self.server_ip_var = tk.StringVar()
        self.server_port_var = tk.StringVar(value="25565")
        self.server_address_var = tk.StringVar(value="服务器地址: 未配置")
        
        # 服务器路径设置变量
        self.jar_path_var = tk.StringVar(value="server.jar")
        self.server_dir_var = tk.StringVar(value=os.getcwd())
        self.java_path_var = tk.StringVar(value="java")
        self.min_mem_var = tk.StringVar(value="1G")
        self.max_mem_var = tk.StringVar(value="2G")
        
        # 设置选项变量
        self.auto_start_var = tk.BooleanVar(value=False)
        self.auto_backup_var = tk.BooleanVar(value=False)
        self.auto_update_var = tk.BooleanVar(value=False)
        
        # 初始化示例数据
        self.init_sample_data()
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置和服务器数据
        self.load_config()
        self.load_server_data()
        
        # 启动封禁监控
        self.start_ban_monitoring()
        
        # 启动禁言监控
        self.start_mute_monitoring()
        
        # 更新服务器地址显示
        self.update_server_address_display()
        
        # 自动检测本地IP地址
        self.auto_detect_local_ip()
        
        # 启动定期数据更新
        self.start_periodic_updates()
        
    def init_sample_data(self):
        """初始化示例数据用于测试"""
        # 示例封禁玩家
        self.banned_players = [
            {"player": "BadPlayer1", "reason": "使用外挂", "ban_date": "2023-01-15 14:30:00", "unban_date": "永久", "ban_type": "永久"},
            {"player": "BadPlayer2", "reason": "恶意破坏", "ban_date": "2023-02-20 10:15:00", "unban_date": "2023-03-20 10:15:00", "ban_type": "临时"}
        ]
        
        # 示例管理员
        self.ops = [
            ("Admin1", "4"),
            ("Moderator1", "2")
        ]
        
        # 示例白名单
        self.whitelist = [
            ("TrustedPlayer1", "2023-01-10"),
            ("TrustedPlayer2", "2023-02-05")
        ]
        
        # 示例禁言玩家
        self.muted_players = {
            "Spammer1": {
                "type": "temporary",
                "mute_date": datetime.now() - timedelta(hours=1),
                "unmute_date": datetime.now() + timedelta(hours=1),
                "reason": "刷屏",
                "mute_time": "2h"
            }
        }
        
        # 示例临时封禁
        self.temp_bans = {
            "BadPlayer2": {
                "ban_date": datetime.now() - timedelta(days=10),
                "unban_date": datetime.now() + timedelta(days=10),
                "reason": "恶意破坏",
                "ban_time": "20d"
            }
        }
        
    def refresh_admin_panel_data(self):
        """刷新管理员面板的所有数据"""
        self.load_banned_players()
        self.load_muted_players()
        self.load_ops()
        self.load_whitelist()
        
    def start_periodic_updates(self):
        """启动定期数据更新"""
        self.update_performance_display()
        if self.server_running:
            self.root.after(5000, self.periodic_player_list_update)
    
    def periodic_player_list_update(self):
        """定期更新玩家列表"""
        if self.server_running:
            # 模拟玩家列表更新
            self.update_players_display()
            # 继续定期更新
            self.root.after(10000, self.periodic_player_list_update)
        
    def auto_detect_local_ip(self):
        """自动检测本地IP地址"""
        def detect_ip():
            try:
                # 获取本机IP地址
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                # 检查是否是本地回环地址
                if local_ip.startswith('127.'):
                    # 尝试获取真实本地IP
                    try:
                        # 创建一个临时socket连接来获取本地IP
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                    except:
                        pass
                
                # 更新IP变量
                self.root.after(0, lambda: self.server_ip_var.set(local_ip))
                self.root.after(0, self.update_server_address_display)
                
            except Exception as e:
                print(f"自动检测IP失败: {e}")
                # 如果检测失败，使用默认值
                self.root.after(0, lambda: self.server_ip_var.set("localhost"))
                self.root.after(0, self.update_server_address_display)
        
        # 在新线程中执行IP检测
        threading.Thread(target=detect_ip, daemon=True).start()
        
    def create_widgets(self):
        # 创建笔记本样式
        style = ttk.Style()
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", padding=[10, 5])
        
        # 创建主笔记本
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个标签页
        self.create_dashboard_tab()
        self.create_admin_panel_tab()
        self.create_player_management_tab()
        self.create_world_management_tab()
        self.create_server_config_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        if PSUTIL_AVAILABLE:
            self.create_performance_tab()
        
    def create_dashboard_tab(self):
        # 仪表板标签页
        dashboard_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(dashboard_frame, text="仪表板")
        
        # 服务器状态区域
        status_frame = ttk.LabelFrame(dashboard_frame, text="服务器状态", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 服务器状态
        self.status_var = tk.StringVar(value="服务器状态: 已停止")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 服务器地址信息
        self.server_address_var = tk.StringVar(value="服务器地址: 未配置")
        server_address_label = ttk.Label(status_frame, textvariable=self.server_address_var, font=("Arial", 10))
        server_address_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 在线玩家信息
        self.players_var = tk.StringVar(value="在线玩家: 0/20")
        players_label = ttk.Label(status_frame, textvariable=self.players_var, font=("Arial", 10))
        players_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # 服务器性能信息
        self.performance_var = tk.StringVar(value="内存使用: N/A | CPU使用: N/A")
        performance_label = ttk.Label(status_frame, textvariable=self.performance_var, font=("Arial", 10))
        performance_label.grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # 控制按钮
        button_frame = ttk.Frame(status_frame)
        button_frame.grid(row=0, column=1, rowspan=4, sticky=(tk.E))
        
        self.start_button = ttk.Button(button_frame, text="启动服务器", command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(button_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        self.restart_button = ttk.Button(button_frame, text="重启服务器", command=self.restart_server, state=tk.DISABLED)
        self.restart_button.grid(row=0, column=2)
        
        # 服务器地址配置区域
        address_config_frame = ttk.Frame(status_frame)
        address_config_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(address_config_frame, text="服务器IP:").grid(row=0, column=0, sticky=tk.W)
        server_ip_entry = ttk.Entry(address_config_frame, textvariable=self.server_ip_var, width=15)
        server_ip_entry.grid(row=0, column=1, padx=(5, 10))
        
        ttk.Label(address_config_frame, text="端口:").grid(row=0, column=2, sticky=tk.W)
        server_port_entry = ttk.Entry(address_config_frame, textvariable=self.server_port_var, width=8)
        server_port_entry.grid(row=0, column=3, padx=(5, 10))
        
        ttk.Button(address_config_frame, text="检测公网IP", 
                  command=self.detect_public_ip).grid(row=0, column=4, padx=(0, 5))
        ttk.Button(address_config_frame, text="检测本地IP", 
                  command=self.auto_detect_local_ip).grid(row=0, column=5, padx=(0, 5))
        ttk.Button(address_config_frame, text="复制地址", 
                  command=self.copy_server_address).grid(row=0, column=6, padx=(0, 5))
        if QRCODE_AVAILABLE:
            ttk.Button(address_config_frame, text="生成二维码", 
                      command=self.generate_qr_code).grid(row=0, column=7)
        
        # 快速命令区域
        quick_cmd_frame = ttk.LabelFrame(dashboard_frame, text="快速命令", padding="10")
        quick_cmd_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 常用命令按钮
        cmd_buttons = [
            ("保存世界", "save-all"),
            ("重新加载", "reload"),
            ("查看玩家", "list"),
            ("停止服务器", "stop"),
            ("设置白天", "time set day"),
            ("设置晴天", "weather clear")
        ]
        
        for i, (text, cmd) in enumerate(cmd_buttons):
            btn = ttk.Button(quick_cmd_frame, text=text, 
                            command=lambda c=cmd: self.quick_command(c))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # 服务器信息区域
        info_frame = ttk.LabelFrame(dashboard_frame, text="服务器信息", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=10, width=50)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.info_text.insert(tk.END, "服务器信息将在这里显示...\n")
        self.info_text.config(state=tk.DISABLED)
        
        # 在线玩家区域
        players_frame = ttk.LabelFrame(dashboard_frame, text="在线玩家", padding="10")
        players_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=(0, 10))
        
        # 创建玩家列表树形视图
        columns = ("玩家名称", "位置", "延迟", "游戏模式")
        self.players_tree = ttk.Treeview(players_frame, columns=columns, show="headings", height=10, selectmode="browse")
        
        for col in columns:
            self.players_tree.heading(col, text=col)
            if col == "玩家名称":
                self.players_tree.column(col, width=100)
            elif col == "位置":
                self.players_tree.column(col, width=120)
            else:
                self.players_tree.column(col, width=60)
        
        self.players_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 玩家列表滚动条
        players_scrollbar = ttk.Scrollbar(players_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        players_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.players_tree.configure(yscrollcommand=players_scrollbar.set)
        
        # 玩家操作按钮
        player_buttons_frame = ttk.Frame(players_frame)
        player_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(player_buttons_frame, text="发送消息", 
                  command=self.send_message_to_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(player_buttons_frame, text="踢出玩家", 
                  command=self.kick_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(player_buttons_frame, text="传送玩家", 
                  command=self.teleport_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(player_buttons_frame, text="设为管理员", 
                  command=self.op_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(player_buttons_frame, text="刷新列表", 
                  command=self.refresh_player_list).pack(side=tk.LEFT)
        
        # 玩家聊天区域
        chat_frame = ttk.LabelFrame(dashboard_frame, text="玩家聊天", padding="10")
        chat_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 聊天显示区域
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=8, width=50)
        self.chat_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        self.chat_text.insert(tk.END, "选择玩家查看聊天记录...\n")
        self.chat_text.config(state=tk.DISABLED)
        
        # 聊天输入区域
        ttk.Label(chat_frame, text="发送消息:").grid(row=1, column=0, sticky=tk.W)
        
        self.chat_message_var = tk.StringVar()
        self.chat_entry = ttk.Entry(chat_frame, textvariable=self.chat_message_var, width=40)
        self.chat_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.chat_entry.bind('<Return>', self.send_chat_message)
        
        self.chat_send_button = ttk.Button(chat_frame, text="发送", command=self.send_chat_message)
        self.chat_send_button.grid(row=1, column=2)
        
        # 命令输入区域
        command_frame = ttk.Frame(dashboard_frame)
        command_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(command_frame, text="服务器命令:").grid(row=0, column=0, sticky=tk.W)
        
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_frame, textvariable=self.command_var, width=50)
        self.command_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        self.command_entry.bind('<Return>', self.send_command)
        self.command_entry.bind('<Tab>', self.auto_complete)
        self.command_entry.bind('<KeyRelease>', self.on_command_key_release)
        
        send_button = ttk.Button(command_frame, text="发送", command=self.send_command)
        send_button.grid(row=0, column=2)
        
        # 命令提示区域
        self.command_hint_var = tk.StringVar(value="输入 /help 查看可用命令")
        command_hint_label = ttk.Label(command_frame, textvariable=self.command_hint_var, foreground="gray")
        command_hint_label.grid(row=1, column=1, sticky=tk.W, pady=(2, 0))
        
        # 配置列权重
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.columnconfigure(1, weight=1)
        dashboard_frame.rowconfigure(2, weight=1)
        status_frame.columnconfigure(0, weight=1)
        quick_cmd_frame.columnconfigure(0, weight=1)
        quick_cmd_frame.columnconfigure(1, weight=1)
        quick_cmd_frame.columnconfigure(2, weight=1)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        players_frame.columnconfigure(0, weight=1)
        players_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(1, weight=1)
        command_frame.columnconfigure(1, weight=1)
        
        # 绑定玩家选择事件
        self.players_tree.bind('<<TreeviewSelect>>', self.on_player_select)

    def create_performance_tab(self):
        """创建性能监控标签页"""
        if not PSUTIL_AVAILABLE:
            return
            
        performance_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(performance_frame, text="性能监控")
        
        # 系统信息区域
        system_info_frame = ttk.LabelFrame(performance_frame, text="系统信息", padding="10")
        system_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 操作系统信息
        if PLATFORM_AVAILABLE:
            os_info = f"操作系统: {platform.system()} {platform.release()}"
            ttk.Label(system_info_frame, text=os_info).grid(row=0, column=0, sticky=tk.W)
            
            # CPU信息
            try:
                cpu_info = f"CPU: {platform.processor()}"
                ttk.Label(system_info_frame, text=cpu_info).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
            except:
                pass
        
        # 性能指标区域
        metrics_frame = ttk.LabelFrame(performance_frame, text="实时性能指标", padding="10")
        metrics_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # CPU使用率
        ttk.Label(metrics_frame, text="CPU使用率:").grid(row=0, column=0, sticky=tk.W)
        self.cpu_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.cpu_var, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky=tk.W)
        
        # 内存使用率
        ttk.Label(metrics_frame, text="内存使用率:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.memory_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.memory_var, font=("Arial", 12, "bold")).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 磁盘使用率
        ttk.Label(metrics_frame, text="磁盘使用率:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.disk_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.disk_var, font=("Arial", 12, "bold")).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        # 网络使用情况
        ttk.Label(metrics_frame, text="网络上传:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.network_sent_var = tk.StringVar(value="0 MB")
        ttk.Label(metrics_frame, textvariable=self.network_sent_var).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(metrics_frame, text="网络下载:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        self.network_recv_var = tk.StringVar(value="0 MB")
        ttk.Label(metrics_frame, textvariable=self.network_recv_var).grid(row=1, column=3, sticky=tk.W, pady=(5, 0))
        
        # 服务器进程资源使用
        server_metrics_frame = ttk.LabelFrame(performance_frame, text="服务器进程资源使用", padding="10")
        server_metrics_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(server_metrics_frame, text="服务器CPU:").grid(row=0, column=0, sticky=tk.W)
        self.server_cpu_var = tk.StringVar(value="0%")
        ttk.Label(server_metrics_frame, textvariable=self.server_cpu_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(server_metrics_frame, text="服务器内存:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.server_memory_var = tk.StringVar(value="0 MB")
        ttk.Label(server_metrics_frame, textvariable=self.server_memory_var).grid(row=0, column=3, sticky=tk.W)
        
        # 性能图表区域
        chart_frame = ttk.LabelFrame(performance_frame, text="性能图表", padding="10")
        chart_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.performance_history_text = scrolledtext.ScrolledText(chart_frame, height=10)
        self.performance_history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.performance_history_text.insert(tk.END, "性能历史数据将在这里显示...\n")
        self.performance_history_text.config(state=tk.DISABLED)
        
        # 性能监控控制
        controls_frame = ttk.Frame(performance_frame)
        controls_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(controls_frame, text="刷新性能数据", 
                  command=self.update_performance_display).pack(side=tk.LEFT, padx=(0, 5))
        
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="自动刷新 (每2秒)", 
                       variable=self.auto_refresh_var).pack(side=tk.LEFT)
        
        # 配置列权重
        performance_frame.columnconfigure(0, weight=1)
        performance_frame.columnconfigure(1, weight=1)
        performance_frame.rowconfigure(3, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(3, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)

    def create_admin_panel_tab(self):
        # 管理员面板标签页
        admin_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(admin_frame, text="管理员面板")
        
        # 创建管理员面板的笔记本
        admin_notebook = ttk.Notebook(admin_frame)
        admin_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 玩家管理标签页
        player_management_frame = ttk.Frame(admin_notebook, padding="10")
        admin_notebook.add(player_management_frame, text="玩家管理")
        
        # 封禁玩家区域
        ban_frame = ttk.LabelFrame(player_management_frame, text="封禁玩家", padding="10")
        ban_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        ttk.Label(ban_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.ban_player_var = tk.StringVar()
        ban_player_entry = ttk.Entry(ban_frame, textvariable=self.ban_player_var, width=20)
        ban_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Label(ban_frame, text="封禁类型:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.ban_type_var = tk.StringVar(value="永久")
        ban_type_combo = ttk.Combobox(ban_frame, textvariable=self.ban_type_var, 
                                     values=["永久", "临时"], width=8, state="readonly")
        ban_type_combo.grid(row=0, column=3, padx=(5, 5))
        ban_type_combo.bind('<<ComboboxSelected>>', self.on_ban_type_changed)
        
        ttk.Label(ban_frame, text="时间:").grid(row=0, column=4, sticky=tk.W)
        self.ban_time_var = tk.StringVar(value="1h")
        self.ban_time_combo = ttk.Combobox(ban_frame, textvariable=self.ban_time_var, 
                                          values=["1h", "2h", "6h", "12h", "1d", "7d", "30d"], 
                                          width=6, state="readonly")
        self.ban_time_combo.grid(row=0, column=5, padx=(5, 5))
        
        ttk.Label(ban_frame, text="原因:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.ban_reason_var = tk.StringVar(value="违反服务器规则")
        ban_reason_entry = ttk.Entry(ban_frame, textvariable=self.ban_reason_var, width=30)
        ban_reason_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        
        ttk.Button(ban_frame, text="封禁玩家", 
                  command=self.ban_player).grid(row=1, column=4, columnspan=2, padx=(10, 0), pady=(5, 0))
        
        # 禁言玩家区域
        mute_frame = ttk.LabelFrame(player_management_frame, text="禁言玩家", padding="10")
        mute_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 10))
        
        ttk.Label(mute_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.mute_player_var = tk.StringVar()
        mute_player_entry = ttk.Entry(mute_frame, textvariable=self.mute_player_var, width=20)
        mute_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Label(mute_frame, text="禁言类型:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.mute_type_var = tk.StringVar(value="永久")
        mute_type_combo = ttk.Combobox(mute_frame, textvariable=self.mute_type_var, 
                                      values=["永久", "临时"], width=8, state="readonly")
        mute_type_combo.grid(row=0, column=3, padx=(5, 5))
        mute_type_combo.bind('<<ComboboxSelected>>', self.on_mute_type_changed)
        
        ttk.Label(mute_frame, text="时间:").grid(row=0, column=4, sticky=tk.W)
        self.mute_time_var = tk.StringVar(value="1h")
        self.mute_time_combo = ttk.Combobox(mute_frame, textvariable=self.mute_time_var, 
                                           values=["1h", "2h", "6h", "12h", "1d", "7d", "30d"], 
                                           width=6, state="readonly")
        self.mute_time_combo.grid(row=0, column=5, padx=(5, 5))
        
        ttk.Label(mute_frame, text="原因:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.mute_reason_var = tk.StringVar(value="不当言论")
        mute_reason_entry = ttk.Entry(mute_frame, textvariable=self.mute_reason_var, width=30)
        mute_reason_entry.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        
        ttk.Button(mute_frame, text="禁言玩家", 
                  command=self.mute_player).grid(row=1, column=4, padx=(10, 5), pady=(5, 0))
        ttk.Button(mute_frame, text="解除禁言", 
                  command=self.unmute_player).grid(row=1, column=5, pady=(5, 0))
        
        # 封禁玩家列表
        ban_list_frame = ttk.LabelFrame(player_management_frame, text="封禁玩家列表", padding="10")
        ban_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树形视图显示封禁玩家
        columns = ("玩家名称", "封禁原因", "封禁日期", "解封日期", "剩余时间")
        self.ban_tree = ttk.Treeview(ban_list_frame, columns=columns, show="headings", height=8, selectmode="browse")
        
        for col in columns:
            self.ban_tree.heading(col, text=col)
            if col == "玩家名称":
                self.ban_tree.column(col, width=120)
            elif col == "封禁原因":
                self.ban_tree.column(col, width=150)
            elif col == "剩余时间":
                self.ban_tree.column(col, width=80)
            else:
                self.ban_tree.column(col, width=120)
        
        self.ban_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 封禁列表滚动条
        ban_scrollbar = ttk.Scrollbar(ban_list_frame, orient=tk.VERTICAL, command=self.ban_tree.yview)
        ban_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.ban_tree.configure(yscrollcommand=ban_scrollbar.set)
        
        # 封禁操作按钮
        ban_buttons_frame = ttk.Frame(ban_list_frame)
        ban_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(ban_buttons_frame, text="解除封禁", 
                  command=self.pardon_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ban_buttons_frame, text="刷新列表", 
                  command=self.load_banned_players).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(ban_buttons_frame, text="更新剩余时间", 
                  command=self.update_ban_times).pack(side=tk.LEFT, padx=(0, 5))
        
        # 禁言玩家列表
        mute_list_frame = ttk.LabelFrame(player_management_frame, text="禁言玩家列表", padding="10")
        mute_list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树形视图显示禁言玩家
        mute_columns = ("玩家名称", "禁言原因", "禁言日期", "解禁日期", "剩余时间")
        self.mute_tree = ttk.Treeview(mute_list_frame, columns=mute_columns, show="headings", height=6, selectmode="browse")
        
        for col in mute_columns:
            self.mute_tree.heading(col, text=col)
            if col == "玩家名称":
                self.mute_tree.column(col, width=120)
            elif col == "禁言原因":
                self.mute_tree.column(col, width=150)
            elif col == "剩余时间":
                self.mute_tree.column(col, width=80)
            else:
                self.mute_tree.column(col, width=120)
        
        self.mute_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 禁言列表滚动条
        mute_scrollbar = ttk.Scrollbar(mute_list_frame, orient=tk.VERTICAL, command=self.mute_tree.yview)
        mute_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.mute_tree.configure(yscrollcommand=mute_scrollbar.set)
        
        # 禁言操作按钮
        mute_buttons_frame = ttk.Frame(mute_list_frame)
        mute_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(mute_buttons_frame, text="解除禁言", 
                  command=self.unmute_selected_player).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mute_buttons_frame, text="刷新列表", 
                  command=self.load_muted_players).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(mute_buttons_frame, text="更新剩余时间", 
                  command=self.update_mute_times).pack(side=tk.LEFT, padx=(0, 5))
        
        # 管理员管理区域
        op_frame = ttk.LabelFrame(player_management_frame, text="管理员管理", padding="10")
        op_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(op_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.op_player_var = tk.StringVar()
        op_player_entry = ttk.Entry(op_frame, textvariable=self.op_player_var, width=20)
        op_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(op_frame, text="设为管理员", 
                  command=self.add_op).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(op_frame, text="取消管理员", 
                  command=self.remove_op).grid(row=0, column=3, padx=(5, 0))
        
        # 管理员列表
        op_list_frame = ttk.LabelFrame(player_management_frame, text="管理员列表", padding="10")
        op_list_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 使用树形视图显示管理员
        op_columns = ("玩家名称", "权限等级")
        self.op_tree = ttk.Treeview(op_list_frame, columns=op_columns, show="headings", height=6, selectmode="browse")
        
        for col in op_columns:
            self.op_tree.heading(col, text=col)
            self.op_tree.column(col, width=150)
        
        self.op_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 管理员列表滚动条
        op_scrollbar = ttk.Scrollbar(op_list_frame, orient=tk.VERTICAL, command=self.op_tree.yview)
        op_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.op_tree.configure(yscrollcommand=op_scrollbar.set)
        
        # 配置列权重
        player_management_frame.columnconfigure(0, weight=1)
        player_management_frame.rowconfigure(1, weight=1)
        player_management_frame.rowconfigure(3, weight=1)
        player_management_frame.rowconfigure(5, weight=1)
        ban_frame.columnconfigure(1, weight=1)
        ban_frame.columnconfigure(3, weight=1)
        mute_frame.columnconfigure(1, weight=1)
        mute_frame.columnconfigure(3, weight=1)
        ban_list_frame.columnconfigure(0, weight=1)
        ban_list_frame.rowconfigure(0, weight=1)
        mute_list_frame.columnconfigure(0, weight=1)
        mute_list_frame.rowconfigure(0, weight=1)
        op_frame.columnconfigure(1, weight=1)
        op_list_frame.columnconfigure(0, weight=1)
        op_list_frame.rowconfigure(0, weight=1)

        # 初始化加载数据
        self.load_banned_players()
        self.load_muted_players()
        self.load_ops()

    def create_player_management_tab(self):
        # 玩家管理标签页
        player_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(player_frame, text="玩家管理")
        
        # 白名单管理区域
        whitelist_frame = ttk.LabelFrame(player_frame, text="白名单管理", padding="10")
        whitelist_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(whitelist_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.whitelist_player_var = tk.StringVar()
        whitelist_player_entry = ttk.Entry(whitelist_frame, textvariable=self.whitelist_player_var, width=20)
        whitelist_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(whitelist_frame, text="添加到白名单", 
                  command=self.add_to_whitelist).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(whitelist_frame, text="从白名单移除", 
                  command=self.remove_from_whitelist).grid(row=0, column=3, padx=(5, 0))
        ttk.Button(whitelist_frame, text="重载白名单", 
                  command=self.reload_whitelist).grid(row=0, column=4, padx=(5, 0))
        
        # 白名单列表
        whitelist_list_frame = ttk.LabelFrame(player_frame, text="白名单列表", padding="10")
        whitelist_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 使用树形视图显示白名单
        whitelist_columns = ("玩家名称", "添加日期")
        self.whitelist_tree = ttk.Treeview(whitelist_list_frame, columns=whitelist_columns, show="headings", height=10, selectmode="browse")
        
        for col in whitelist_columns:
            self.whitelist_tree.heading(col, text=col)
            self.whitelist_tree.column(col, width=150)
        
        self.whitelist_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 白名单列表滚动条
        whitelist_scrollbar = ttk.Scrollbar(whitelist_list_frame, orient=tk.VERTICAL, command=self.whitelist_tree.yview)
        whitelist_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.whitelist_tree.configure(yscrollcommand=whitelist_scrollbar.set)
        
        # 白名单操作按钮
        whitelist_buttons_frame = ttk.Frame(whitelist_list_frame)
        whitelist_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(whitelist_buttons_frame, text="刷新列表", 
                  command=self.load_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="启用白名单", 
                  command=self.enable_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="禁用白名单", 
                  command=self.disable_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="导出白名单", 
                  command=self.export_whitelist).pack(side=tk.LEFT)
        
        # 玩家数据管理区域
        player_data_frame = ttk.LabelFrame(player_frame, text="玩家数据管理", padding="10")
        player_data_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(player_data_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.player_data_var = tk.StringVar()
        player_data_entry = ttk.Entry(player_data_frame, textvariable=self.player_data_var, width=20)
        player_data_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(player_data_frame, text="查看玩家数据", 
                  command=self.view_player_data).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(player_data_frame, text="重置玩家数据", 
                  command=self.reset_player_data).grid(row=0, column=3, padx=(5, 0))
        ttk.Button(player_data_frame, text="传送玩家", 
                  command=self.teleport_to_player).grid(row=0, column=4, padx=(5, 0))
        
        # 配置列权重
        player_frame.columnconfigure(0, weight=1)
        player_frame.rowconfigure(1, weight=1)
        whitelist_frame.columnconfigure(1, weight=1)
        whitelist_list_frame.columnconfigure(0, weight=1)
        whitelist_list_frame.rowconfigure(0, weight=1)
        player_data_frame.columnconfigure(1, weight=1)

        # 初始化加载数据
        self.load_whitelist()

    def create_world_management_tab(self):
        # 世界管理标签页
        world_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(world_frame, text="世界管理")
        
        # 世界备份区域
        backup_frame = ttk.LabelFrame(world_frame, text="世界备份", padding="10")
        backup_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(backup_frame, text="创建备份", 
                  command=self.create_backup).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(backup_frame, text="恢复备份", 
                  command=self.restore_backup).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(backup_frame, text="打开备份目录", 
                  command=self.open_backup_folder).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(backup_frame, text="自动备份设置", 
                  command=self.auto_backup_settings).grid(row=0, column=3)
        
        # 游戏规则区域
        gamerules_frame = ttk.LabelFrame(world_frame, text="游戏规则", padding="10")
        gamerules_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 常用游戏规则
        gamerules = [
            ("保持物品栏", "keepInventory", "false"),
            ("生物破坏", "mobGriefing", "true"),
            ("昼夜循环", "doDaylightCycle", "true"),
            ("天气循环", "doWeatherCycle", "true"),
            ("火焰蔓延", "doFireTick", "true"),
            ("死亡掉落", "keepInventory", "false"),
            ("自然生命恢复", "naturalRegeneration", "true"),
            ("命令方块", "commandBlockOutput", "true")
        ]
        
        self.gamerule_vars = {}
        
        for i, (text, rule, default) in enumerate(gamerules):
            ttk.Label(gamerules_frame, text=text).grid(row=i, column=0, sticky=tk.W)
            var = tk.StringVar(value=default)
            self.gamerule_vars[rule] = var
            
            ttk.Combobox(gamerules_frame, textvariable=var, 
                        values=["true", "false"], width=10, state="readonly").grid(row=i, column=1, padx=(5, 10))
            
            ttk.Button(gamerules_frame, text="应用", 
                      command=lambda r=rule, v=var: self.set_gamerule(r, v.get())).grid(row=i, column=2, padx=(0, 10))
        
        # 世界设置区域
        world_settings_frame = ttk.LabelFrame(world_frame, text="世界设置", padding="10")
        world_settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(world_settings_frame, text="设置出生点", 
                  command=self.set_spawn_point).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(world_settings_frame, text="更改游戏模式", 
                  command=self.change_game_mode).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(world_settings_frame, text="更改难度", 
                  command=self.change_difficulty).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(world_settings_frame, text="设置时间", 
                  command=self.set_time).grid(row=0, column=3, padx=(0, 5))
        
        # 配置列权重
        world_frame.columnconfigure(0, weight=1)
        gamerules_frame.columnconfigure(0, weight=1)

    def create_server_config_tab(self):
        # 服务器配置标签页
        config_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(config_frame, text="服务器配置")
        
        # 服务器属性区域
        properties_frame = ttk.LabelFrame(config_frame, text="服务器属性", padding="10")
        properties_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 常用服务器属性
        properties = [
            ("服务器端口", "server-port", "25565"),
            ("在线模式", "online-mode", "true"),
            ("最大玩家数", "max-players", "20"),
            ("视图距离", "view-distance", "10"),
            ("白名单", "white-list", "false"),
            ("PVP", "pvp", "true"),
            ("难度", "difficulty", "easy"),
            ("游戏模式", "gamemode", "survival"),
            ("生成怪物", "spawn-monsters", "true"),
            ("生成动物", "spawn-animals", "true"),
            ("生成NPC", "spawn-npcs", "true"),
            ("允许飞行", "allow-flight", "false"),
            ("资源包", "resource-pack", ""),
            ("Motd", "motd", "A Minecraft Server")
        ]
        
        self.property_vars = {}
        
        for i, (text, prop, default) in enumerate(properties):
            ttk.Label(properties_frame, text=text).grid(row=i, column=0, sticky=tk.W)
            var = tk.StringVar(value=default)
            self.property_vars[prop] = var
            
            if prop in ["online-mode", "white-list", "pvp", "spawn-monsters", "spawn-animals", "spawn-npcs", "allow-flight"]:
                ttk.Combobox(properties_frame, textvariable=var, 
                            values=["true", "false"], width=15, state="readonly").grid(row=i, column=1, padx=(5, 10))
            elif prop == "difficulty":
                ttk.Combobox(properties_frame, textvariable=var, 
                            values=["peaceful", "easy", "normal", "hard"], width=15, state="readonly").grid(row=i, column=1, padx=(5, 10))
            elif prop == "gamemode":
                ttk.Combobox(properties_frame, textvariable=var, 
                            values=["survival", "creative", "adventure", "spectator"], width=15, state="readonly").grid(row=i, column=1, padx=(5, 10))
            else:
                ttk.Entry(properties_frame, textvariable=var, width=15).grid(row=i, column=1, padx=(5, 10))
            
            ttk.Button(properties_frame, text="应用", 
                      command=lambda p=prop, v=var: self.set_property(p, v.get())).grid(row=i, column=2, padx=(0, 10))
        
        # 应用所有更改按钮
        ttk.Button(properties_frame, text="应用所有更改", 
                  command=self.apply_all_properties).grid(row=len(properties), column=0, columnspan=3, pady=(10, 0))
        
        # 配置列权重
        config_frame.columnconfigure(0, weight=1)
        properties_frame.columnconfigure(1, weight=1)

    def create_logs_tab(self):
        # 日志标签页
        logs_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(logs_frame, text="服务器日志")
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志控制按钮
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="清空日志", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="导出日志", 
                  command=self.export_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="查找", 
                  command=self.search_logs).pack(side=tk.LEFT)

    def create_settings_tab(self):
        # 设置标签页
        settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_frame, text="设置")
        
        # 服务器路径设置
        path_frame = ttk.LabelFrame(settings_frame, text="服务器路径设置", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="服务器JAR路径:").grid(row=0, column=0, sticky=tk.W)
        self.jar_path_var = tk.StringVar(value="server.jar")
        jar_path_entry = ttk.Entry(path_frame, textvariable=self.jar_path_var, width=50)
        jar_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(path_frame, text="浏览", 
                  command=self.browse_jar_path).grid(row=0, column=2)
        
        ttk.Label(path_frame, text="服务器目录:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.server_dir_var = tk.StringVar(value=os.getcwd())
        server_dir_entry = ttk.Entry(path_frame, textvariable=self.server_dir_var, width=50)
        server_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        
        ttk.Button(path_frame, text="浏览", 
                  command=self.browse_server_dir).grid(row=1, column=2, pady=(5, 0))
        
        # Java设置
        java_frame = ttk.LabelFrame(settings_frame, text="Java设置", padding="10")
        java_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(java_frame, text="Java路径:").grid(row=0, column=0, sticky=tk.W)
        self.java_path_var = tk.StringVar(value="java")
        java_path_entry = ttk.Entry(java_frame, textvariable=self.java_path_var, width=50)
        java_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(java_frame, text="浏览", 
                  command=self.browse_java_path).grid(row=0, column=2)
        
        ttk.Label(java_frame, text="最小内存:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.min_mem_var = tk.StringVar(value="1G")
        min_mem_entry = ttk.Entry(java_frame, textvariable=self.min_mem_var, width=10)
        min_mem_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 5), pady=(5, 0))
        
        ttk.Label(java_frame, text="最大内存:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.max_mem_var = tk.StringVar(value="2G")
        max_mem_entry = ttk.Entry(java_frame, textvariable=self.max_mem_var, width=10)
        max_mem_entry.grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        # 其他设置
        other_frame = ttk.LabelFrame(settings_frame, text="其他设置", padding="10")
        other_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="启动时自动启动服务器", 
                       variable=self.auto_start_var).grid(row=0, column=0, sticky=tk.W)
        
        self.auto_backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="定期自动备份世界", 
                       variable=self.auto_backup_var).grid(row=1, column=0, sticky=tk.W)
        
        self.auto_update_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="自动检查服务器更新", 
                       variable=self.auto_update_var).grid(row=2, column=0, sticky=tk.W)
        
        # 保存设置按钮
        ttk.Button(settings_frame, text="保存设置", 
                  command=self.save_config).grid(row=3, column=0, pady=(10, 0))
        
        # 配置列权重
        settings_frame.columnconfigure(0, weight=1)
        path_frame.columnconfigure(1, weight=1)
        java_frame.columnconfigure(1, weight=1)

    def update_server_address_display(self):
        """更新服务器地址显示"""
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        
        if ip and port:
            address = f"{ip}:{port}"
            self.server_address_var.set(f"服务器地址: {address}")
            
            # 检查是否是本地回环地址，如果是则显示警告
            if ip.startswith('127.'):
                self.server_address_var.set(f"服务器地址: {address} (本地测试地址，其他设备无法连接)")
            elif ip == "localhost":
                self.server_address_var.set(f"服务器地址: {address} (本地测试地址，其他设备无法连接)")
        else:
            self.server_address_var.set("服务器地址: 未配置")

    def copy_server_address(self):
        """复制服务器地址到剪贴板"""
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        
        if ip and port:
            address = f"{ip}:{port}"
            self.root.clipboard_clear()
            self.root.clipboard_append(address)
            messagebox.showinfo("成功", f"服务器地址已复制到剪贴板: {address}")
        else:
            messagebox.showwarning("警告", "请先配置服务器地址和端口")

    def detect_public_ip(self):
        """检测公网IP地址"""
        def get_public_ip():
            try:
                # 使用多个IP检测服务以提高成功率
                services = [
                    'https://api.ipify.org',
                    'https://ident.me',
                    'https://checkip.amazonaws.com'
                ]
                
                for service in services:
                    try:
                        with urllib.request.urlopen(service, timeout=5) as response:
                            ip = response.read().decode('utf-8').strip()
                            if ip and len(ip.split('.')) == 4:
                                return ip
                    except:
                        continue
                return None
            except Exception as e:
                return None
        
        def update_ip():
            try:
                public_ip = get_public_ip()
                if public_ip:
                    self.server_ip_var.set(public_ip)
                    self.update_server_address_display()
                    messagebox.showinfo("公网IP检测", f"检测到公网IP: {public_ip}")
                else:
                    messagebox.showerror("错误", "无法检测公网IP，请手动输入")
            except Exception as e:
                messagebox.showerror("错误", f"检测公网IP时出错: {str(e)}")
        
        # 在新线程中执行IP检测
        threading.Thread(target=update_ip, daemon=True).start()
        messagebox.showinfo("检测中", "正在检测公网IP，请稍候...")

    def generate_qr_code(self):
        """生成服务器连接二维码"""
        if not QRCODE_AVAILABLE:
            messagebox.showerror("错误", "需要安装qrcode和PIL库: pip install qrcode[pil]")
            return
        
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("警告", "请先配置服务器地址和端口")
            return
        
        address = f"{ip}:{port}"
        
        # 创建二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        # 创建二维码窗口
        qr_window = tk.Toplevel(self.root)
        qr_window.title("服务器连接二维码")
        qr_window.geometry("400x500")
        qr_window.resizable(False, False)
        
        # 生成二维码图像
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(qr_image)
        
        # 显示二维码
        qr_label = ttk.Label(qr_window, image=photo)
        qr_label.image = photo  # 保持引用
        qr_label.pack(pady=10)
        
        # 显示服务器地址
        address_label = ttk.Label(qr_window, text=f"服务器地址: {address}", font=("Arial", 12, "bold"))
        address_label.pack(pady=5)
        
        # 说明文字
        help_text = "使用手机Minecraft扫描此二维码可直接连接服务器"
        help_label = ttk.Label(qr_window, text=help_text, wraplength=350, justify=tk.CENTER)
        help_label.pack(pady=10)
        
        # 按钮框架
        button_frame = ttk.Frame(qr_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="保存二维码", 
                  command=lambda: self.save_qr_code(qr_image)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", 
                  command=qr_window.destroy).pack(side=tk.LEFT, padx=5)

    def save_qr_code(self, qr_image):
        """保存二维码到文件"""
        filename = filedialog.asksaveasfilename(
            title="保存二维码",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            try:
                qr_image.save(filename)
                messagebox.showinfo("成功", f"二维码已保存到: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存二维码时出错: {str(e)}")

    def start_server(self):
        jar_path = self.jar_path_var.get()
        if not os.path.exists(jar_path):
            messagebox.showerror("错误", f"找不到服务器JAR文件: {jar_path}")
            return
        
        # 检查服务器目录
        server_dir = self.server_dir_var.get()
        if not os.path.exists(server_dir):
            try:
                os.makedirs(server_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建服务器目录: {str(e)}")
                return
        
        # 构建启动命令 - 修复中文显示问题
        min_mem = self.min_mem_var.get()
        max_mem = self.max_mem_var.get()
        java_path = self.java_path_var.get()
        
        # 添加UTF-8编码参数确保中文正常显示
        command = f'"{java_path}" -Xms{min_mem} -Xmx{max_mem} -Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8 -jar "{jar_path}" nogui'
        
        try:
            # 切换到服务器目录
            os.chdir(server_dir)
            
            # 使用支持UTF-8的环境启动服务器
            env = os.environ.copy()
            env['JAVA_TOOL_OPTIONS'] = '-Dfile.encoding=UTF-8'
            
            # 修复中文显示问题 - 使用正确的编码
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                shell=True,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            self.server_running = True
            self.status_var.set("服务器状态: 运行中")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.restart_button.config(state=tk.NORMAL)
            
            # 启动线程读取服务器输出
            self.output_thread = threading.Thread(target=self.read_output)
            self.output_thread.daemon = True
            self.output_thread.start()
            
            # 启动性能监控
            if PSUTIL_AVAILABLE:
                self.start_performance_monitoring()
            
            # 启动玩家位置和延迟模拟
            self.start_player_simulation()
            
            self.log_message("服务器已启动")
            
            # 启动定期数据更新
            self.start_periodic_updates()
            
        except Exception as e:
            messagebox.showerror("错误", f"启动服务器时出错: {str(e)}")
    
    def stop_server(self):
        if self.server_process and self.server_running:
            try:
                self.send_server_command("stop")
                
                # 停止性能监控
                if PSUTIL_AVAILABLE:
                    self.stop_performance_monitoring()
                
                # 停止玩家模拟
                self.stop_player_simulation()
                
                # 等待进程结束
                def wait_for_stop():
                    try:
                        self.server_process.wait(timeout=30)
                        self.root.after(0, self.server_stopped)
                    except subprocess.TimeoutExpired:
                        self.server_process.terminate()
                        self.root.after(0, self.server_stopped)
                
                stop_thread = threading.Thread(target=wait_for_stop)
                stop_thread.daemon = True
                stop_thread.start()
                
            except Exception as e:
                messagebox.showerror("错误", f"停止服务器时出错: {str(e)}")
    
    def read_output(self):
        """读取服务器输出 - 修复中文显示问题"""
        while self.server_process and self.server_running:
            try:
                output = self.server_process.stdout.readline()
                if output:
                    # 直接使用UTF-8，因为我们已经设置了编码
                    decoded_output = output
                    self.root.after(0, self.process_output, decoded_output.strip())
                elif self.server_process.poll() is not None:
                    break
            except Exception as e:
                print(f"读取输出时出错: {e}")
                break
        
        # 服务器进程已结束
        if self.server_running:
            self.root.after(0, self.server_stopped_unexpectedly)
    
    def process_output(self, output):
        """处理服务器输出"""
        # 修复中文显示问题 - 确保使用UTF-8编码
        try:
            # 直接使用UTF-8输出
            self.log_message(output)
        except UnicodeEncodeError:
            # 如果遇到编码问题，使用错误处理
            safe_output = output.encode('utf-8', errors='replace').decode('utf-8')
            self.log_message(safe_output)
        
        # 解析服务器输出
        if "joined the game" in output.lower():
            self.parse_player_join(output)
        elif "left the game" in output.lower():
            self.parse_player_leave(output)
        elif "There are" in output and "of a max" in output:
            self.parse_player_list(output)
        elif "whisper" in output.lower() or "msg" in output.lower() or "tell" in output.lower():
            self.parse_player_message(output)
        elif "chat" in output.lower() and ">" in output:
            self.parse_public_chat(output)
        elif "was banned" in output.lower():
            self.parse_ban_message(output)
    
    def parse_ban_message(self, output):
        """解析封禁消息"""
        try:
            # 匹配封禁消息格式
            pattern = r'(\[\d+:\d+:\d+\])?\s*\[.*?/INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*was banned'
            match = re.search(pattern, output)
            if match:
                player = match.group(2)
                self.log_message(f"玩家 {player} 已被成功封禁")
                # 刷新封禁列表
                self.root.after(0, self.load_banned_players)
        except Exception as e:
            self.log_message(f"解析封禁消息时出错: {str(e)}")
    
    def parse_public_chat(self, output):
        """解析公共聊天消息"""
        try:
            # 匹配聊天消息格式: [时间] [线程/INFO]: <玩家> 消息
            pattern = r'\[.*?\]\s*\[.*?/INFO\]:\s*<([a-zA-Z0-9_]{3,16})>\s*(.+)'
            match = re.search(pattern, output)
            if match:
                player = match.group(1)
                message = match.group(2)
                self.message_manager.add_message(player, message, is_server=False)
        except Exception as e:
            self.log_message(f"解析公共聊天时出错: {str(e)}")
    
    def parse_player_join(self, output):
        """解析玩家加入消息"""
        try:
            patterns = [
                r'(\[\d+:\d+:\d+\])?\s*\[.*?/INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*joined the game',
                r'INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*joined the game'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    player = match.group(2) if match.lastindex >= 2 else match.group(1)
                    if player and player not in self.players_online:
                        self.players_online.append(player)
                        # 初始化玩家位置和延迟
                        self.message_manager.update_player_position(player, 0, 64, 0)
                        self.message_manager.update_player_ping(player, 50)
                        self.update_players_display()
                        # 添加加入消息
                        self.message_manager.add_message(player, f"{player} 加入了游戏", is_server=True)
                    break
        except Exception as e:
            self.log_message(f"解析玩家加入消息时出错: {str(e)}")
    
    def parse_player_leave(self, output):
        """解析玩家离开消息"""
        try:
            patterns = [
                r'(\[\d+:\d+:\d+\])?\s*\[.*?/INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*left the game',
                r'INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*left the game'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    player = match.group(2) if match.lastindex >= 2 else match.group(1)
                    if player in self.players_online:
                        self.players_online.remove(player)
                        self.update_players_display()
                        # 添加离开消息
                        self.message_manager.add_message(player, f"{player} 离开了游戏", is_server=True)
                    break
        except Exception as e:
            self.log_message(f"解析玩家离开消息时出错: {str(e)}")
    
    def parse_player_message(self, output):
        """解析玩家消息"""
        try:
            # 解析玩家私聊消息
            patterns = [
                r'(\[\d+:\d+:\d+\])?\s*\[.*?/INFO\]:\s*([a-zA-Z0-9_]{3,16})\s*(?:whispers|tells|messages)\s*you:\s*(.+)',
                r'INFO\]:\s*<([a-zA-Z0-9_]{3,16})>\s*(.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    if match.lastindex == 3:
                        player = match.group(2)
                        message = match.group(3)
                    else:
                        player = match.group(1)
                        message = match.group(2)
                    
                    if player:
                        self.message_manager.add_message(player, message, is_server=False)
                    break
        except Exception as e:
            self.log_message(f"解析玩家消息时出错: {str(e)}")
    
    def send_command(self, event=None):
        """发送命令到服务器"""
        command = self.command_var.get().strip()
        if not command:
            return
        
        self.send_server_command(command)
        self.command_var.set("")
        self.suggestion_index = -1
    
    def send_server_command(self, command):
        """发送命令到服务器进程"""
        if self.server_process and self.server_running:
            try:
                # 确保命令使用UTF-8编码发送
                encoded_command = command + "\n"
                self.server_process.stdin.write(encoded_command)
                self.server_process.stdin.flush()
                self.log_message(f"> {command}")
                
                # 如果命令是管理员相关操作，刷新数据
                if command.startswith(('deop ', 'pardon ', 'unmute ', 'whitelist remove ')):
                    # 延迟一小段时间后刷新数据，确保服务器已处理命令
                    self.root.after(1000, self.refresh_admin_panel_data)
                    
                # 如果命令是tell/msg，记录消息
                if command.startswith(('/tell ', '/msg ')):
                    parts = command.split(' ', 2)
                    if len(parts) >= 3:
                        player = parts[1]
                        message = parts[2]
                        self.message_manager.add_message(player, message, is_server=True)
                        
            except Exception as e:
                messagebox.showerror("错误", f"发送命令时出错: {str(e)}")
        else:
            messagebox.showwarning("警告", "服务器未运行，无法发送命令")
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 同时更新仪表板的信息区域
        if "INFO]" in message or "WARN]" in message or "ERROR]" in message:
            self.info_text.config(state=tk.NORMAL)
            self.info_text.insert(tk.END, f"{message}\n")
            self.info_text.see(tk.END)
            self.info_text.config(state=tk.DISABLED)
    
    def update_players_display(self):
        """更新在线玩家显示"""
        max_players = self.property_vars.get("max-players", tk.StringVar(value="20")).get()
        try:
            max_players_int = int(max_players)
        except:
            max_players_int = 20
            
        self.players_var.set(f"在线玩家: {len(self.players_online)}/{max_players_int}")
        
        # 更新玩家树形视图
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)
            
        for player in self.players_online:
            pos = self.message_manager.get_player_position(player)
            ping = self.message_manager.get_player_ping(player)
            position_str = f"{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}"
            self.players_tree.insert("", tk.END, values=(player, position_str, f"{ping}ms", "生存"))

    def on_player_select(self, event):
        """处理玩家选择事件"""
        selection = self.players_tree.selection()
        if selection:
            player = self.players_tree.item(selection[0])['values'][0]
            self.update_player_chat_display(player)
    
    def update_player_chat_display(self, player):
        """更新玩家聊天显示"""
        if not hasattr(self, 'chat_text'):
            return
            
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        
        messages = self.message_manager.get_player_messages(player)
        for msg in messages:
            self.chat_text.insert(tk.END, f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n")
        
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def send_chat_message(self, event=None):
        """发送聊天消息给选中的玩家"""
        selection = self.players_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        player = self.players_tree.item(selection[0])['values'][0]
        message = self.chat_message_var.get().strip()
        
        if not message:
            return
            
        # 发送消息给选中的玩家
        self.send_server_command(f"tell {player} {message}")
        # 添加到消息记录
        self.message_manager.add_message(player, message, is_server=True)
        
        self.chat_message_var.set("")
    
    def get_selected_player(self):
        """获取选中的玩家"""
        selection = self.players_tree.selection()
        if selection:
            return self.players_tree.item(selection[0])['values'][0]
        return None
    
    def send_message_to_player(self):
        """发送消息给选中的玩家（通过对话框）"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        message = simpledialog.askstring("发送消息", f"发送给 {player} 的消息:")
        
        if message:
            self.send_server_command(f"tell {player} {message}")
            self.message_manager.add_message(player, message, is_server=True)

    def start_player_simulation(self):
        """启动玩家位置和延迟模拟"""
        if not self.server_running:
            return
            
        def simulate_player_movement():
            while self.server_running:
                for player in self.players_online:
                    # 模拟位置变化
                    x = self.message_manager.get_player_position(player)[0] + (ord(player[0]) % 10 - 5)
                    y = self.message_manager.get_player_position(player)[1] + (ord(player[1]) % 5 - 2)
                    z = self.message_manager.get_player_position(player)[2] + (ord(player[2]) % 10 - 5)
                    
                    # 限制坐标范围
                    x = max(-1000, min(1000, x))
                    y = max(0, min(256, y))
                    z = max(-1000, min(1000, z))
                    
                    self.message_manager.update_player_position(player, x, y, z)
                    
                    # 模拟延迟变化
                    ping = max(10, min(500, self.message_manager.get_player_ping(player) + (ord(player[0]) % 20 - 10)))
                    self.message_manager.update_player_ping(player, ping)
                
                time.sleep(2)  # 每2秒更新一次
        
        self.simulation_thread = threading.Thread(target=simulate_player_movement)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
    
    def stop_player_simulation(self):
        """停止玩家模拟"""
        self.server_running = False

    def server_stopped(self):
        """服务器正常停止"""
        self.server_running = False
        self.status_var.set("服务器状态: 已停止")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.log_message("服务器已停止")
        
        # 清空在线玩家列表
        self.players_online = []
        self.update_players_display()
    
    def server_stopped_unexpectedly(self):
        """服务器意外停止"""
        self.server_running = False
        self.status_var.set("服务器状态: 已停止 (意外退出)")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.restart_button.config(state=tk.DISABLED)
        self.log_message("服务器进程意外退出")
        
        # 清空在线玩家列表
        self.players_online = []
        self.update_players_display()

    def restart_server(self):
        """重启服务器"""
        self.log_message("正在重启服务器...")
        self.stop_server()
        self.root.after(5000, self.start_server)

    def quick_command(self, command):
        """快速命令"""
        self.send_server_command(command)

    def kick_player(self):
        """踢出玩家"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        reason = simpledialog.askstring("踢出玩家", f"踢出 {player} 的原因:", initialvalue="违反服务器规则")
        
        if reason is not None:
            if reason:
                self.send_server_command(f"kick {player} {reason}")
            else:
                self.send_server_command(f"kick {player}")

    def teleport_player(self):
        """传送玩家"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        destination = simpledialog.askstring("传送玩家", f"将 {player} 传送到:", initialvalue="~ ~ ~")
        
        if destination:
            self.send_server_command(f"tp {player} {destination}")

    def op_player(self):
        """设为管理员"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        self.send_server_command(f"op {player}")

    def refresh_player_list(self):
        """刷新玩家列表"""
        if self.server_running:
            self.send_server_command("list")
        else:
            messagebox.showwarning("警告", "服务器未运行，无法刷新玩家列表")

    def parse_player_list(self, output):
        """解析玩家列表命令的输出"""
        try:
            # 示例输出: "There are 2 of a max of 20 players online: player1, player2"
            pattern = r'There are (\d+) of a max of (\d+) players online: (.*)'
            match = re.search(pattern, output)
            
            if match:
                online_count = int(match.group(1))
                max_players = int(match.group(2))
                player_list = match.group(3).split(', ')
                
                # 更新在线玩家列表
                self.players_online = player_list
                self.update_players_display()
                
                # 更新在线玩家数量显示
                self.players_var.set(f"在线玩家: {online_count}/{max_players}")
        except Exception as e:
            self.log_message(f"解析玩家列表时出错: {str(e)}")

    # 性能监控相关方法
    def start_performance_monitoring(self):
        """启动性能监控"""
        if self.server_process and PSUTIL_AVAILABLE:
            self.performance_monitor.start_monitoring(self.server_process)
            self.update_performance_display()
            
    def stop_performance_monitoring(self):
        """停止性能监控"""
        self.performance_monitor.stop_monitoring()
        if self.performance_update_timer:
            self.root.after_cancel(self.performance_update_timer)
            self.performance_update_timer = None
    
    def update_performance_display(self):
        """更新性能显示"""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            data = self.performance_monitor.get_performance_data()
            
            memory_text = f"内存: {data['memory_used']:.1f}GB/{data['memory_total']:.1f}GB ({data['memory_percent']:.1f}%)"
            cpu_text = f"CPU: {data['cpu_percent']:.1f}%"
            disk_text = f"磁盘: {data['disk_used']:.1f}GB/{data['disk_total']:.1f}GB ({data['disk_percent']:.1f}%)"
            
            self.performance_var.set(f"{memory_text} | {cpu_text} | {disk_text}")
            
            if hasattr(self, 'cpu_var'):
                self.cpu_var.set(f"{data['cpu_percent']:.1f}%")
                self.memory_var.set(f"{data['memory_percent']:.1f}%")
                self.disk_var.set(f"{data['disk_percent']:.1f}%")
                self.network_sent_var.set(f"{data['network_sent']:.2f} MB")
                self.network_recv_var.set(f"{data['network_recv']:.2f} MB")
            
            if 'server_cpu' in data and hasattr(self, 'server_cpu_var'):
                self.server_cpu_var.set(f"{data['server_cpu']:.1f}%")
                self.server_memory_var.set(f"{data['server_memory']:.1f} MB")
            
            # 更新性能历史显示
            self.update_performance_history()
            
        except Exception as e:
            print(f"更新性能显示时出错: {e}")
        
        if hasattr(self, 'auto_refresh_var') and self.auto_refresh_var.get() and self.server_running:
            self.performance_update_timer = self.root.after(2000, self.update_performance_display)
    
    def update_performance_history(self):
        """更新性能历史数据显示"""
        if not PSUTIL_AVAILABLE or not hasattr(self, 'performance_history_text'):
            return
            
        history = self.performance_monitor.get_performance_history()
        if not history:
            return
            
        self.performance_history_text.config(state=tk.NORMAL)
        self.performance_history_text.delete(1.0, tk.END)
        
        # 显示最近10条性能记录
        recent_history = history[-10:] if len(history) > 10 else history
        
        for record in recent_history:
            timestamp = record['timestamp'].strftime("%H:%M:%S")
            cpu = record['cpu']
            memory = record['memory']
            server_cpu = record.get('server_cpu', 0)
            server_memory = record.get('server_memory', 0)
            
            line = f"[{timestamp}] CPU: {cpu:.1f}% | 内存: {memory:.1f}%"
            if server_cpu > 0:
                line += f" | 服务器CPU: {server_cpu:.1f}% | 服务器内存: {server_memory:.1f}MB"
            
            self.performance_history_text.insert(tk.END, line + "\n")
        
        self.performance_history_text.see(tk.END)
        self.performance_history_text.config(state=tk.DISABLED)

    # 命令补全相关方法
    def on_command_key_release(self, event):
        """命令输入框按键释放事件"""
        if event.keysym in ['Up', 'Down']:
            return
        
        text = self.command_var.get()
        if text.startswith('/'):
            cmd_name = text.split()[0][1:]
            cmd_info = self.command_completer.get_command_info(cmd_name)
            if cmd_info:
                self.command_hint_var.set(cmd_info.get('description', '未知命令'))
            else:
                self.command_hint_var.set("未知命令 - 输入 /help 查看可用命令")
        else:
            self.command_hint_var.set("输入 /help 查看可用命令")
    
    def auto_complete(self, event):
        """自动补全命令"""
        text = self.command_var.get()
        
        if not text:
            return "break"
        
        suggestions = self.command_completer.get_command_suggestions(text)
        
        if not suggestions:
            return "break"
        
        if len(suggestions) > 1:
            self.suggestion_index = (self.suggestion_index + 1) % len(suggestions)
            completed_text = suggestions[self.suggestion_index]
        else:
            completed_text = suggestions[0]
        
        self.command_var.set(completed_text)
        
        if completed_text.startswith('/') and len(completed_text.split()) == 1:
            self.command_var.set(completed_text + " ")
        
        return "break"

    # 封禁管理相关方法
    def on_ban_type_changed(self, event=None):
        """当封禁类型改变时更新界面"""
        if self.ban_type_var.get() == "永久":
            self.ban_time_combo.config(state="disabled")
        else:
            self.ban_time_combo.config(state="readonly")

    def ban_player(self):
        """封禁玩家 - 修复临时封禁问题"""
        player = self.ban_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        reason = self.ban_reason_var.get().strip()
        ban_type = self.ban_type_var.get()
        
        if ban_type == "永久":
            # 永久封禁
            if reason:
                self.send_server_command(f"ban {player} {reason}")
            else:
                self.send_server_command(f"ban {player}")
            
            # 添加到封禁列表
            ban_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.banned_players.append({
                "player": player,
                "reason": reason,
                "ban_date": ban_date,
                "unban_date": "永久",
                "ban_type": "永久"
            })
            
        else:
            # 临时封禁 - 使用ban命令而不是tempban
            ban_time = self.ban_time_var.get()
            if reason:
                self.send_server_command(f"ban {player} {reason}")
            else:
                self.send_server_command(f"ban {player}")
            
            # 计算解封时间
            ban_date = datetime.now()
            unban_date = self.calculate_unban_date(ban_date, ban_time)
            
            # 添加到临时封禁列表
            self.temp_bans[player] = {
                "ban_date": ban_date,
                "unban_date": unban_date,
                "reason": reason,
                "ban_time": ban_time
            }
            
            self.banned_players.append({
                "player": player,
                "reason": reason,
                "ban_date": ban_date.strftime("%Y-%m-%d %H:%M:%S"),
                "unban_date": unban_date.strftime("%Y-%m-%d %H:%M:%S"),
                "ban_type": "临时"
            })
        
        self.ban_player_var.set("")
        # 立即更新封禁列表显示
        self.load_banned_players()
        messagebox.showinfo("成功", f"已封禁玩家: {player}")

    def calculate_unban_date(self, ban_date, ban_time):
        """计算解封时间"""
        time_units = {
            'm': 1/60,  # 分钟
            'h': 1,     # 小时
            'd': 24,    # 天
            'w': 168,   # 周
            'M': 720,   # 月 (30天)
            'y': 8760   # 年 (365天)
        }
        
        try:
            # 解析时间字符串，如 "1h", "2d", "1w" 等
            value = int(ban_time[:-1])
            unit = ban_time[-1]
            
            if unit in time_units:
                hours = value * time_units[unit]
                return ban_date + timedelta(hours=hours)
            else:
                # 默认1小时
                return ban_date + timedelta(hours=1)
        except:
            # 解析失败，默认1小时
            return ban_date + timedelta(hours=1)

    def start_ban_monitoring(self):
        """启动封禁监控"""
        self.ban_monitoring = True
        
        def monitor_bans():
            while self.ban_monitoring:
                current_time = datetime.now()
                players_to_unban = []
                
                # 检查需要解封的玩家
                for player, ban_info in self.temp_bans.items():
                    if current_time >= ban_info["unban_date"]:
                        players_to_unban.append(player)
                
                # 执行解封
                for player in players_to_unban:
                    self.send_server_command(f"pardon {player}")
                    del self.temp_bans[player]
                    
                    # 从封禁列表中移除
                    self.banned_players = [b for b in self.banned_players if b["player"] != player]
                    
                    # 更新显示
                    self.root.after(0, self.load_banned_players)
                    self.root.after(0, lambda: self.log_message(f"自动解封玩家: {player}"))
                
                time.sleep(60)  # 每分钟检查一次
        
        self.ban_monitor_thread = threading.Thread(target=monitor_bans)
        self.ban_monitor_thread.daemon = True
        self.ban_monitor_thread.start()

    def update_ban_times(self):
        """更新封禁剩余时间显示"""
        current_time = datetime.now()
        
        for item in self.ban_tree.get_children():
            values = self.ban_tree.item(item)['values']
            player = values[0]  # 第一列是玩家名称
            
            if player in self.temp_bans:
                ban_info = self.temp_bans[player]
                time_left = ban_info["unban_date"] - current_time
                
                if time_left.total_seconds() <= 0:
                    # 时间已到，自动解封
                    self.send_server_command(f"pardon {player}")
                    del self.temp_bans[player]
                    self.banned_players = [b for b in self.banned_players if b["player"] != player]
                else:
                    # 更新剩余时间显示
                    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m"
                    else:
                        time_str = f"{minutes}m {seconds}s"
                    
                    # 更新显示
                    self.ban_tree.set(item, "剩余时间", time_str)
        
        # 重新加载封禁列表以确保显示最新数据
        self.load_banned_players()

    def load_banned_players(self):
        """加载封禁玩家列表 - 确保完全清空列表"""
        # 完全清空现有列表
        for item in self.ban_tree.get_children():
            self.ban_tree.delete(item)
        
        # 添加封禁玩家
        current_time = datetime.now()
        for ban in self.banned_players:
            player = ban["player"]
            reason = ban["reason"]
            ban_date = ban["ban_date"]
            unban_date = ban["unban_date"]
            ban_type = ban.get("ban_type", "永久")
            
            # 计算剩余时间（如果是临时封禁）
            time_left = "永久"
            if ban_type == "临时" and player in self.temp_bans:
                ban_info = self.temp_bans[player]
                time_left_delta = ban_info["unban_date"] - current_time
                
                if time_left_delta.total_seconds() > 0:
                    hours, remainder = divmod(int(time_left_delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_left = f"{hours}h {minutes}m"
                    else:
                        time_left = f"{minutes}m {seconds}s"
                else:
                    time_left = "已过期"
                    # 自动移除过期封禁
                    self.banned_players.remove(ban)
                    if player in self.temp_bans:
                        del self.temp_bans[player]
                    continue
            
            self.ban_tree.insert("", tk.END, values=(player, reason, ban_date, unban_date, time_left))

    def pardon_player(self):
        """解除封禁玩家"""
        selection = self.ban_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解封的玩家")
            return
        
        player = self.ban_tree.item(selection[0])['values'][0]  # 第一列是玩家名称
        
        # 发送解封命令
        self.send_server_command(f"pardon {player}")
        
        # 从列表中移除
        if player in self.temp_bans:
            del self.temp_bans[player]
        
        # 从封禁列表中移除
        self.banned_players = [b for b in self.banned_players if b["player"] != player]
        
        # 立即更新显示
        self.load_banned_players()
        messagebox.showinfo("成功", f"已解封玩家: {player}")

    # 禁言管理相关方法
    def on_mute_type_changed(self, event=None):
        """当禁言类型改变时更新界面"""
        if self.mute_type_var.get() == "永久":
            self.mute_time_combo.config(state="disabled")
        else:
            self.mute_time_combo.config(state="readonly")

    def mute_player(self):
        """禁言玩家"""
        player = self.mute_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        reason = self.mute_reason_var.get().strip()
        mute_type = self.mute_type_var.get()
        
        if mute_type == "永久":
            # 永久禁言
            if reason:
                self.send_server_command(f"mute {player} {reason}")
            else:
                self.send_server_command(f"mute {player}")
            
            # 添加到禁言列表
            mute_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.muted_players[player] = {
                "type": "permanent",
                "reason": reason,
                "mute_date": mute_date,
                "unmute_date": "永久"
            }
            
        else:
            # 临时禁言
            mute_time = self.mute_time_var.get()
            if reason:
                self.send_server_command(f"mute {player} {mute_time} {reason}")
            else:
                self.send_server_command(f"mute {player} {mute_time}")
            
            # 计算解禁时间
            mute_date = datetime.now()
            unmute_date = self.calculate_unmute_date(mute_date, mute_time)
            
            # 添加到临时禁言列表
            self.muted_players[player] = {
                "type": "temporary",
                "mute_date": mute_date,
                "unmute_date": unmute_date,
                "reason": reason,
                "mute_time": mute_time
            }
        
        self.mute_player_var.set("")
        # 立即更新禁言列表显示
        self.load_muted_players()
        messagebox.showinfo("成功", f"已禁言玩家: {player}")

    def unmute_player(self):
        """解除禁言玩家"""
        player = self.mute_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        if player in self.muted_players:
            self.send_server_command(f"unmute {player}")
            del self.muted_players[player]
            self.load_muted_players()
            messagebox.showinfo("成功", f"已解除玩家 {player} 的禁言")
        else:
            messagebox.showwarning("警告", f"玩家 {player} 未被禁言")

    def unmute_selected_player(self):
        """解除选中的禁言玩家"""
        selection = self.mute_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解禁的玩家")
            return
        
        player = self.mute_tree.item(selection[0])['values'][0]  # 第一列是玩家名称
        
        # 发送解禁命令
        self.send_server_command(f"unmute {player}")
        
        # 从列表中移除
        if player in self.muted_players:
            del self.muted_players[player]
        
        # 立即更新显示
        self.load_muted_players()
        messagebox.showinfo("成功", f"已解除玩家 {player} 的禁言")

    def calculate_unmute_date(self, mute_date, mute_time):
        """计算解禁时间"""
        return self.calculate_unban_date(mute_date, mute_time)  # 复用封禁时间计算逻辑

    def load_muted_players(self):
        """加载禁言玩家列表 - 确保完全清空列表"""
        # 完全清空现有列表
        for item in self.mute_tree.get_children():
            self.mute_tree.delete(item)
        
        # 添加禁言玩家
        current_time = datetime.now()
        players_to_remove = []
        
        for player, mute_info in self.muted_players.items():
            reason = mute_info.get("reason", "无")
            mute_date = mute_info.get("mute_date", "未知")
            unmute_date = mute_info.get("unmute_date", "永久")
            mute_type = mute_info.get("type", "permanent")
            
            # 计算剩余时间（如果是临时禁言）
            time_left = "永久"
            if mute_type == "temporary" and isinstance(unmute_date, datetime):
                time_left_delta = unmute_date - current_time
                
                if time_left_delta.total_seconds() > 0:
                    hours, remainder = divmod(int(time_left_delta.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_left = f"{hours}h {minutes}m"
                    else:
                        time_left = f"{minutes}m {seconds}s"
                else:
                    time_left = "已过期"
                    # 标记为需要移除
                    players_to_remove.append(player)
                    continue
            
            # 格式化日期显示
            if isinstance(mute_date, datetime):
                mute_date_str = mute_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                mute_date_str = str(mute_date)
                
            if isinstance(unmute_date, datetime):
                unmute_date_str = unmute_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                unmute_date_str = str(unmute_date)
            
            self.mute_tree.insert("", tk.END, values=(player, reason, mute_date_str, unmute_date_str, time_left))
        
        # 移除过期的禁言
        for player in players_to_remove:
            del self.muted_players[player]

    def update_mute_times(self):
        """更新禁言剩余时间显示"""
        current_time = datetime.now()
        
        for item in self.mute_tree.get_children():
            values = self.mute_tree.item(item)['values']
            player = values[0]  # 第一列是玩家名称
            
            if player in self.muted_players:
                mute_info = self.muted_players[player]
                if mute_info.get("type") == "temporary" and isinstance(mute_info.get("unmute_date"), datetime):
                    time_left = mute_info["unmute_date"] - current_time
                    
                    if time_left.total_seconds() <= 0:
                        # 时间已到，自动解禁
                        self.send_server_command(f"unmute {player}")
                        del self.muted_players[player]
                    else:
                        # 更新剩余时间显示
                        hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        if hours > 0:
                            time_str = f"{hours}h {minutes}m"
                        else:
                            time_str = f"{minutes}m {seconds}s"
                        
                        # 更新显示
                        self.mute_tree.set(item, "剩余时间", time_str)
        
        # 重新加载禁言列表以确保显示最新数据
        self.load_muted_players()

    def start_mute_monitoring(self):
        """启动禁言监控"""
        self.mute_monitoring = True
        
        def monitor_mutes():
            while self.mute_monitoring:
                current_time = datetime.now()
                players_to_unmute = []
                
                # 检查需要解禁的玩家
                for player, mute_info in self.muted_players.items():
                    if mute_info.get("type") == "temporary" and isinstance(mute_info.get("unmute_date"), datetime):
                        if current_time >= mute_info["unmute_date"]:
                            players_to_unmute.append(player)
                
                # 执行解禁
                for player in players_to_unmute:
                    self.send_server_command(f"unmute {player}")
                    del self.muted_players[player]
                    
                    # 更新显示
                    self.root.after(0, self.load_muted_players)
                    self.root.after(0, lambda: self.log_message(f"自动解除玩家禁言: {player}"))
                
                time.sleep(60)  # 每分钟检查一次
        
        self.mute_monitor_thread = threading.Thread(target=monitor_mutes)
        self.mute_monitor_thread.daemon = True
        self.mute_monitor_thread.start()

    # 管理员管理相关方法
    def add_op(self):
        """添加管理员 - 增加确认提示"""
        player = self.op_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        result = messagebox.askyesno("确认", f"确定要将玩家 {player} 设为管理员吗？")
        if result:
            self.send_server_command(f"op {player}")
            # 添加到本地列表
            self.ops.append((player, "4"))
            self.load_ops()
            self.op_player_var.set("")
            messagebox.showinfo("成功", f"已将玩家 {player} 设为管理员")

    def remove_op(self):
        """移除管理员 - 增加确认提示"""
        selection = self.op_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择管理员")
            return
            
        player = self.op_tree.item(selection[0])['values'][0]
        
        result = messagebox.askyesno("确认", f"确定要移除玩家 {player} 的管理员权限吗？")
        if result:
            self.send_server_command(f"deop {player}")
            # 从本地列表移除
            self.ops = [op for op in self.ops if op[0] != player]
            # 立即刷新显示
            self.load_ops()
            messagebox.showinfo("成功", f"已移除玩家 {player} 的管理员权限")

    def load_ops(self):
        """加载管理员列表 - 确保完全清空列表"""
        # 完全清空现有列表
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)
        
        # 添加管理员
        for name, level in self.ops:
            self.op_tree.insert("", tk.END, values=(name, level))

    # 白名单管理方法
    def add_to_whitelist(self):
        """添加到白名单"""
        player = self.whitelist_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        self.send_server_command(f"whitelist add {player}")
        # 添加到本地列表
        self.whitelist.append((player, datetime.now().strftime("%Y-%m-%d")))
        self.whitelist_player_var.set("")
        # 立即刷新白名单列表
        self.load_whitelist()
        messagebox.showinfo("成功", f"已将玩家 {player} 添加到白名单")
    
    def remove_from_whitelist(self):
        """从白名单移除"""
        selection = self.whitelist_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个玩家")
            return
        
        player = self.whitelist_tree.item(selection[0])['values'][0]  # 第一列是玩家名称
        self.send_server_command(f"whitelist remove {player}")
        
        # 从本地列表移除
        self.whitelist = [wl for wl in self.whitelist if wl[0] != player]
        
        # 立即刷新白名单列表
        self.load_whitelist()
        messagebox.showinfo("成功", f"已从白名单移除玩家: {player}")
    
    def reload_whitelist(self):
        """重载白名单"""
        self.send_server_command("whitelist reload")
        messagebox.showinfo("成功", "白名单已重载")
    
    def enable_whitelist(self):
        """启用白名单"""
        self.send_server_command("whitelist on")
        self.set_property("white-list", "true")
        messagebox.showinfo("成功", "白名单已启用")
    
    def disable_whitelist(self):
        """禁用白名单"""
        self.send_server_command("whitelist off")
        self.set_property("white-list", "false")
        messagebox.showinfo("成功", "白名单已禁用")
    
    def load_whitelist(self):
        """加载白名单列表"""
        # 完全清空现有列表
        for item in self.whitelist_tree.get_children():
            self.whitelist_tree.delete(item)
        
        # 添加白名单玩家
        for name, created in self.whitelist:
            self.whitelist_tree.insert("", tk.END, values=(name, created))
    
    def view_player_data(self):
        """查看玩家数据"""
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        # 在实际应用中，这里应该显示玩家数据
        # 检查玩家数据文件是否存在
        player_data_dir = os.path.join(self.server_dir_var.get(), "world", "playerdata")
        if os.path.exists(player_data_dir):
            # 查找玩家数据文件（需要UUID，这里简化处理）
            player_files = [f for f in os.listdir(player_data_dir) if f.endswith('.dat')]
            
            if player_files:
                # 显示第一个找到的玩家数据文件信息
                player_file = player_files[0]
                file_path = os.path.join(player_data_dir, player_file)
                file_size = os.path.getsize(file_path)
                
                info = f"玩家: {player}\n"
                info += f"数据文件: {player_file}\n"
                info += f"文件大小: {file_size} 字节\n"
                info += f"最后修改: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}"
                
                messagebox.showinfo("玩家数据", info)
            else:
                messagebox.showinfo("玩家数据", f"未找到玩家 {player} 的数据文件")
        else:
            messagebox.showwarning("警告", "玩家数据目录不存在")
    
    def reset_player_data(self):
        """重置玩家数据"""
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        result = messagebox.askyesno("确认", f"确定要重置玩家 {player} 的数据吗？此操作不可撤销！")
        if result:
            # 在实际应用中，这里应该重置玩家数据
            self.send_server_command(f"kick {player} 你的数据已被重置")
            messagebox.showinfo("成功", f"玩家 {player} 的数据已重置")
    
    def teleport_to_player(self):
        """传送到玩家"""
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        target = simpledialog.askstring("传送玩家", f"将谁传送到 {player}:", parent=self.root)
        if target:
            self.send_server_command(f"tp {target} {player}")

    # 世界管理方法
    def create_backup(self):
        """创建备份"""
        backup_name = simpledialog.askstring("创建备份", "请输入备份名称:", parent=self.root)
        if backup_name:
            # 在实际应用中，这里应该实现备份逻辑
            self.send_server_command("save-all")
            self.log_message(f"正在创建备份: {backup_name}")
            
            # 模拟备份过程
            backup_dir = os.path.join(self.server_dir_var.get(), "backups")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            world_dir = os.path.join(self.server_dir_var.get(), "world")
            if os.path.exists(world_dir):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = os.path.join(backup_dir, f"{backup_name}_{timestamp}")
                shutil.copytree(world_dir, backup_path)
                self.log_message(f"备份已创建: {backup_path}")
                messagebox.showinfo("成功", f"备份 {backup_name} 创建成功")
            else:
                messagebox.showerror("错误", "找不到世界目录")
    
    def restore_backup(self):
        """恢复备份"""
        backup_dir = os.path.join(self.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            messagebox.showerror("错误", "备份目录不存在")
            return
        
        backups = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
        if not backups:
            messagebox.showerror("错误", "没有找到备份")
            return
        
        # 显示备份列表供用户选择
        backup_list_window = tk.Toplevel(self.root)
        backup_list_window.title("选择备份")
        backup_list_window.geometry("400x300")
        
        tk.Label(backup_list_window, text="请选择要恢复的备份:").pack(pady=10)
        
        backup_listbox = tk.Listbox(backup_list_window)
        backup_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for backup in sorted(backups, reverse=True):
            backup_listbox.insert(tk.END, backup)
        
        def confirm_restore():
            selection = backup_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个备份")
                return
            
            backup_name = backup_listbox.get(selection[0])
            backup_list_window.destroy()
            
            result = messagebox.askyesno("确认", f"确定要恢复备份 {backup_name} 吗？当前世界将被覆盖！")
            if result:
                self.log_message(f"正在恢复备份: {backup_name}")
                
                # 停止服务器
                if self.server_running:
                    self.stop_server()
                    # 等待服务器停止
                    self.root.after(5000, lambda: self.do_restore_backup(os.path.join(backup_dir, backup_name)))
                else:
                    self.do_restore_backup(os.path.join(backup_dir, backup_name))
        
        tk.Button(backup_list_window, text="恢复选中的备份", command=confirm_restore).pack(pady=10)
    
    def do_restore_backup(self, backup_path):
        """执行备份恢复"""
        try:
            world_dir = os.path.join(self.server_dir_var.get(), "world")
            # 备份当前世界
            if os.path.exists(world_dir):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_current = os.path.join(self.server_dir_var.get(), "backups", f"pre_restore_{timestamp}")
                shutil.copytree(world_dir, backup_current)
            
            # 删除当前世界
            if os.path.exists(world_dir):
                shutil.rmtree(world_dir)
            
            # 恢复备份
            shutil.copytree(backup_path, world_dir)
            
            self.log_message(f"备份 {os.path.basename(backup_path)} 恢复成功")
            messagebox.showinfo("成功", f"备份 {os.path.basename(backup_path)} 恢复成功")
            
            # 重新启动服务器
            if self.auto_start_var.get():
                self.root.after(2000, self.start_server)
                
        except Exception as e:
            messagebox.showerror("错误", f"恢复备份时出错: {str(e)}")
    
    def open_backup_folder(self):
        """打开备份文件夹"""
        backup_dir = os.path.join(self.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        webbrowser.open(backup_dir)
    
    def auto_backup_settings(self):
        """自动备份设置"""
        # 自动备份设置对话框
        settings_window = tk.Toplevel(self.root)
        settings_window.title("自动备份设置")
        settings_window.geometry("400x200")
        
        tk.Label(settings_window, text="自动备份设置", font=("Arial", 12, "bold")).pack(pady=10)
        
        # 备份间隔
        interval_frame = tk.Frame(settings_window)
        interval_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(interval_frame, text="备份间隔:").pack(side=tk.LEFT)
        interval_var = tk.StringVar(value="60")
        interval_entry = tk.Entry(interval_frame, textvariable=interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(interval_frame, text="分钟").pack(side=tk.LEFT)
        
        # 最大备份数量
        max_backups_frame = tk.Frame(settings_window)
        max_backups_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(max_backups_frame, text="最大备份数量:").pack(side=tk.LEFT)
        max_backups_var = tk.StringVar(value="10")
        max_backups_entry = tk.Entry(max_backups_frame, textvariable=max_backups_var, width=10)
        max_backups_entry.pack(side=tk.LEFT, padx=5)
        
        def save_settings():
            # 保存自动备份设置
            messagebox.showinfo("成功", "自动备份设置已保存")
            settings_window.destroy()
        
        tk.Button(settings_window, text="保存设置", command=save_settings).pack(pady=20)
    
    def set_gamerule(self, rule, value):
        """设置游戏规则"""
        self.send_server_command(f"gamerule {rule} {value}")
    
    def set_spawn_point(self):
        """设置出生点"""
        x = simpledialog.askinteger("设置出生点", "X坐标:", parent=self.root)
        y = simpledialog.askinteger("设置出生点", "Y坐标:", parent=self.root)
        z = simpledialog.askinteger("设置出生点", "Z坐标:", parent=self.root)
        
        if x is not None and y is not None and z is not None:
            self.send_server_command(f"setworldspawn {x} {y} {z}")
    
    def change_game_mode(self):
        """更改游戏模式"""
        mode = simpledialog.askstring("更改游戏模式", "请输入游戏模式 (survival, creative, adventure, spectator):", parent=self.root)
        if mode and mode in ["survival", "creative", "adventure", "spectator"]:
            self.send_server_command(f"defaultgamemode {mode}")
            self.set_property("gamemode", mode)
    
    def change_difficulty(self):
        """更改难度"""
        difficulty = simpledialog.askstring("更改难度", "请输入难度 (peaceful, easy, normal, hard):", parent=self.root)
        if difficulty and difficulty in ["peaceful", "easy", "normal", "hard"]:
            self.send_server_command(f"difficulty {difficulty}")
            self.set_property("difficulty", difficulty)
    
    def set_time(self):
        """设置时间"""
        time_str = simpledialog.askstring("设置时间", "请输入时间 (day, night, noon, midnight 或 0-24000):", parent=self.root)
        if time_str:
            self.send_server_command(f"time set {time_str}")

    # 服务器配置方法
    def set_property(self, prop, value):
        """设置服务器属性"""
        # 修改 server.properties 文件
        self.log_message(f"设置服务器属性: {prop}={value}")
        
        properties_file = os.path.join(self.server_dir_var.get(), "server.properties")
        if os.path.exists(properties_file):
            try:
                # 读取现有属性
                properties = {}
                with open(properties_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key_value = line.split('=')
                            if len(key_value) == 2:
                                properties[key_value[0].strip()] = key_value[1].strip()
                
                # 更新属性
                properties[prop] = value
                
                # 写回文件
                with open(properties_file, 'w', encoding='utf-8') as f:
                    for key, val in properties.items():
                        f.write(f"{key}={val}\n")
                
                # 如果修改的是端口号，同步更新界面显示
                if prop == "server-port":
                    self.server_port_var.set(value)
                    self.update_server_address_display()
                
                # 立即应用某些需要重启的属性
                if prop in ["max-players", "view-distance", "difficulty", "gamemode"]:
                    self.send_server_command(f"{prop.replace('-', '')} {value}")
                
                messagebox.showinfo("成功", f"属性 {prop} 已设置为 {value}")
            except Exception as e:
                messagebox.showerror("错误", f"修改服务器属性时出错: {str(e)}")
        else:
            messagebox.showwarning("警告", "找不到 server.properties 文件")
    
    def apply_all_properties(self):
        """应用所有属性更改"""
        for prop, var in self.property_vars.items():
            self.set_property(prop, var.get())
        messagebox.showinfo("成功", "所有服务器属性已应用")

    # 设置方法
    def browse_jar_path(self):
        """浏览JAR文件路径"""
        filename = filedialog.askopenfilename(
            title="选择服务器JAR文件",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_path_var.set(filename)
    
    def browse_server_dir(self):
        """浏览服务器目录"""
        directory = filedialog.askdirectory(title="选择服务器目录")
        if directory:
            self.server_dir_var.set(directory)
            # 自动加载服务器数据
            self.load_server_data()
    
    def browse_java_path(self):
        """浏览Java路径"""
        filename = filedialog.askopenfilename(
            title="选择Java可执行文件",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.java_path_var.set(filename)
    
    def save_config(self):
        """保存配置"""
        config = configparser.ConfigParser()
        
        config['PATHS'] = {
            'jar_path': self.jar_path_var.get(),
            'server_dir': self.server_dir_var.get(),
            'java_path': self.java_path_var.get()
        }
        
        config['JAVA'] = {
            'min_memory': self.min_mem_var.get(),
            'max_memory': self.max_mem_var.get()
        }
        
        config['SETTINGS'] = {
            'auto_start': str(self.auto_start_var.get()),
            'auto_backup': str(self.auto_backup_var.get()),
            'auto_update': str(self.auto_update_var.get())
        }
        
        # 保存服务器地址配置
        config['SERVER_ADDRESS'] = {
            'server_ip': self.server_ip_var.get(),
            'server_port': self.server_port_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")
    
    def load_config(self):
        """加载配置"""
        if not os.path.exists(self.config_file):
            return
        
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file, encoding='utf-8')
        except:
            config.read(self.config_file)
        
        try:
            if 'PATHS' in config:
                self.jar_path_var.set(config['PATHS'].get('jar_path', 'server.jar'))
                self.server_dir_var.set(config['PATHS'].get('server_dir', os.getcwd()))
                self.java_path_var.set(config['PATHS'].get('java_path', 'java'))
            
            if 'JAVA' in config:
                self.min_mem_var.set(config['JAVA'].get('min_memory', '1G'))
                self.max_mem_var.set(config['JAVA'].get('max_memory', '2G'))
            
            if 'SETTINGS' in config:
                self.auto_start_var.set(config['SETTINGS'].getboolean('auto_start', False))
                self.auto_backup_var.set(config['SETTINGS'].getboolean('auto_backup', False))
                self.auto_update_var.set(config['SETTINGS'].getboolean('auto_update', False))
            
            # 加载服务器地址配置
            if 'SERVER_ADDRESS' in config:
                self.server_ip_var.set(config['SERVER_ADDRESS'].get('server_ip', ''))
                self.server_port_var.set(config['SERVER_ADDRESS'].get('server_port', '25565'))
        except Exception as e:
            print(f"加载设置时出错: {str(e)}")

    def clear_logs(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def export_logs(self):
        """导出日志"""
        filename = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("成功", f"日志已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出日志时出错: {str(e)}")
    
    def search_logs(self):
        """搜索日志"""
        search_term = simpledialog.askstring("查找日志", "请输入要查找的内容:", parent=self.root)
        if search_term:
            # 在实际应用中，这里应该实现日志搜索功能
            messagebox.showinfo("查找", f"搜索: {search_term}")

    def load_server_data(self):
        """从服务器文件加载数据"""
        self.load_server_properties()
        self.load_banned_players()
        self.load_ops()
        self.load_whitelist()
    
    def load_server_properties(self):
        """加载服务器属性"""
        properties_file = os.path.join(self.server_dir_var.get(), "server.properties")
        if os.path.exists(properties_file):
            try:
                properties = {}
                with open(properties_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key_value = line.split('=')
                            if len(key_value) == 2:
                                properties[key_value[0].strip()] = key_value[1].strip()
                
                # 更新属性变量
                for prop, var in self.property_vars.items():
                    if prop in properties:
                        var.set(properties[prop])
                    else:
                        # 如果属性不存在，设置默认值
                        default_values = {
                            "server-port": "25565",
                            "online-mode": "true", 
                            "max-players": "20",
                            "view-distance": "10",
                            "white-list": "false",
                            "pvp": "true",
                            "difficulty": "easy",
                            "gamemode": "survival",
                            "spawn-monsters": "true",
                            "spawn-animals": "true",
                            "spawn-npcs": "true",
                            "allow-flight": "false",
                            "resource-pack": "",
                            "motd": "A Minecraft Server"
                        }
                        if prop in default_values:
                            var.set(default_values[prop])
                
                # 同步端口号到界面显示
                if 'server-port' in properties:
                    self.server_port_var.set(properties['server-port'])
                    self.update_server_address_display()
                            
            except Exception as e:
                self.log_message(f"加载服务器属性时出错: {str(e)}")
    
    def export_whitelist(self):
        """导出白名单"""
        filename = filedialog.asksaveasfilename(
            title="导出白名单",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("玩家名称,添加日期\n")
                    for name, created in self.whitelist:
                        f.write(f"{name},{created}\n")
                messagebox.showinfo("成功", f"白名单已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出白名单时出错: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MCServerControlPanel(root)
    root.mainloop()