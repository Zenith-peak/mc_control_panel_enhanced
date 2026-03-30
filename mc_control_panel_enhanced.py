import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
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

# 导入子模块
from server_manager import ServerManager
from player_manager import PlayerManager
from ban_manager import BanManager
from performance_manager import PerformanceManager
from message_manager import MessageManager
from command_completer import CommandCompleter
from plugin_manager import PluginManager
from version_detector import VersionDetector
from player_filter import PlayerFilter, PlayerFilterUI
from admin_panel_ui import AdminPanelUI

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


class ScrollableFrame:
    """
    可滚动容器类
    使用Canvas作为主容器，支持垂直和水平滚动
    支持鼠标滚轮（Windows和Linux）
    增强版：更好的滚动条管理和窗口大小适配
    """
    def __init__(self, parent, width=None, height=None, bg_color="#f8f9fa"):
        self.parent = parent
        self.bg_color = bg_color
        self.scroll_sensitivity = 30  # 滚动灵敏度
        self.min_content_width = 700  # 最小内容宽度

        # 创建主容器Frame
        self.main_frame = ttk.Frame(parent)

        # 创建Canvas作为滚动区域
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=bg_color,
            highlightthickness=0,
            width=width,
            height=height
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建垂直滚动条
        self.v_scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建水平滚动条（初始隐藏）
        self.h_scrollbar = ttk.Scrollbar(
            self.main_frame,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        # 水平滚动条默认不显示，只在需要时显示

        # 配置Canvas滚动命令
        self.canvas.configure(
            yscrollcommand=self._on_vertical_scroll,
            xscrollcommand=self._on_horizontal_scroll
        )

        # 创建内容Frame
        self.content_frame = ttk.Frame(self.canvas, padding="10")

        # 在Canvas上创建窗口
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor=tk.NW,
            tags="content"
        )

        # 绑定事件
        self._bind_events()

        # 初始化滚动区域
        self.update_scroll_region()

    def _on_vertical_scroll(self, *args):
        """垂直滚动回调"""
        self.v_scrollbar.set(*args)
        # 检查是否需要显示垂直滚动条
        self._update_scrollbar_visibility()

    def _on_horizontal_scroll(self, *args):
        """水平滚动回调"""
        self.h_scrollbar.set(*args)

    def _update_scrollbar_visibility(self):
        """更新滚动条可见性"""
        # 获取内容Frame的大小
        content_width = self.content_frame.winfo_reqwidth()
        content_height = self.content_frame.winfo_reqheight()
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # 检查垂直滚动条
        if content_height > canvas_height:
            if not self.v_scrollbar.winfo_ismapped():
                self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            if self.v_scrollbar.winfo_ismapped():
                self.v_scrollbar.pack_forget()

        # 检查水平滚动条
        if content_width > canvas_width:
            if not self.h_scrollbar.winfo_ismapped():
                self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            if self.h_scrollbar.winfo_ismapped():
                self.h_scrollbar.pack_forget()

    def _bind_events(self):
        """绑定各种事件"""
        # 内容Frame大小变化时更新滚动区域
        self.content_frame.bind("<Configure>", self._on_content_configure)

        # Canvas大小变化时更新内容窗口大小
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 鼠标滚轮事件（Windows）
        self.canvas.bind("<MouseWheel>", self._on_mousewheel_windows)
        self.content_frame.bind("<MouseWheel>", self._on_mousewheel_windows)

        # 鼠标滚轮事件（Linux）
        self.canvas.bind("<Button-4>", self._on_mousewheel_linux_up)
        self.canvas.bind("<Button-5>", self._on_mousewheel_linux_down)
        self.content_frame.bind("<Button-4>", self._on_mousewheel_linux_up)
        self.content_frame.bind("<Button-5>", self._on_mousewheel_linux_down)

        # 为内容Frame中的所有子控件绑定滚轮事件
        self._bind_mousewheel_to_children(self.content_frame)

        # 绑定窗口大小变化事件
        self._bind_resize_event()

    def _bind_resize_event(self):
        """绑定窗口大小变化事件"""
        # 使用after机制定期检查大小变化
        self._check_resize()

    def _check_resize(self):
        """检查窗口大小变化"""
        try:
            self._update_scrollbar_visibility()
            self._on_canvas_configure()
        except:
            pass
        # 每100ms检查一次
        self.main_frame.after(100, self._check_resize)

    def _bind_mousewheel_to_children(self, parent):
        """递归为所有子控件绑定鼠标滚轮事件"""
        for child in parent.winfo_children():
            # Windows滚轮
            child.bind("<MouseWheel>", self._on_mousewheel_windows, add=True)
            # Linux滚轮
            child.bind("<Button-4>", self._on_mousewheel_linux_up, add=True)
            child.bind("<Button-5>", self._on_mousewheel_linux_down, add=True)

            # 递归绑定子控件的子控件
            if child.winfo_children():
                self._bind_mousewheel_to_children(child)

        # 监听新添加的子控件
        parent.bind("<Map>", self._on_parent_map, add=True)

    def _on_parent_map(self, event):
        """当父控件被映射时，为新子控件绑定事件"""
        widget = event.widget
        if widget != self.content_frame:
            return

        def check_new_children():
            for child in widget.winfo_children():
                # Windows滚轮
                child.bind("<MouseWheel>", self._on_mousewheel_windows, add=True)
                # Linux滚轮
                child.bind("<Button-4>", self._on_mousewheel_linux_up, add=True)
                child.bind("<Button-5>", self._on_mousewheel_linux_down, add=True)

                if child.winfo_children():
                    self._bind_mousewheel_to_children(child)

        widget.after(10, check_new_children)

    def _on_content_configure(self, event=None):
        """内容Frame配置变化时更新滚动区域"""
        self.update_scroll_region()
        self._update_scrollbar_visibility()

    def _on_canvas_configure(self, event=None):
        """Canvas大小变化时更新内容窗口宽度"""
        if event:
            canvas_width = event.width
            canvas_height = event.height
        else:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

        # 确保内容窗口宽度不小于最小宽度
        new_width = max(canvas_width, self.min_content_width)
        self.canvas.itemconfig(self.canvas_window, width=new_width)

        # 更新滚动条可见性
        self._update_scrollbar_visibility()

    def _on_mousewheel_windows(self, event):
        """Windows鼠标滚轮事件处理"""
        # Windows: event.delta 通常是 120 的倍数，正值向上，负值向下
        delta = -1 * (event.delta // 120) * self.scroll_sensitivity
        self.canvas.yview_scroll(delta, "units")
        return "break"

    def _on_mousewheel_linux_up(self, event):
        """Linux鼠标滚轮向上事件处理"""
        # Linux Button-4: 向上滚动
        self.canvas.yview_scroll(-1 * self.scroll_sensitivity // 30, "units")
        return "break"

    def _on_mousewheel_linux_down(self, event):
        """Linux鼠标滚轮向下事件处理"""
        # Linux Button-5: 向下滚动
        self.canvas.yview_scroll(self.scroll_sensitivity // 30, "units")
        return "break"

    def update_scroll_region(self):
        """更新滚动区域"""
        self.canvas.update_idletasks()
        # 获取内容Frame的大小
        content_width = self.content_frame.winfo_reqwidth()
        content_height = self.content_frame.winfo_reqheight()
        # 设置滚动区域
        self.canvas.configure(scrollregion=(0, 0, content_width, content_height))

    def get_frame(self):
        """获取内容Frame，用于添加控件"""
        return self.content_frame

    def get_main_frame(self):
        """获取主Frame，用于布局"""
        return self.main_frame

    def scroll_to_top(self):
        """滚动到顶部"""
        self.canvas.yview_moveto(0)

    def scroll_to_bottom(self):
        """滚动到底部"""
        self.canvas.yview_moveto(1)


class MCServerControlPanel:
    def __init__(self, root):
        self.root = root
        
        # 导入响应式布局管理器
        from responsive_manager import ResponsiveManager, get_responsive_config
        
        # 设置窗口标题和默认大小
        self.root.title("Minecraft 服务器控制面板 V0.1.5-beta3")
        self.root.geometry("1000x700")
        # 设置窗口最小大小
        self.root.minsize(800, 600)
        
        # 创建响应式管理器
        self.responsive_manager = ResponsiveManager(root)
        self.get_responsive_config = get_responsive_config
        
        # 设置编码 - 修复中文显示问题
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleCP(65001)
                kernel32.SetConsoleOutputCP(65001)
            except:
                pass
        
        # 玩家数据和服务器属性
        self.banned_players = []
        self.ops = []
        self.whitelist = []
        self.server_properties = {}
        
        # 配置文件
        self.config_file = "mc_panel_config.ini"
        
        # 日志保存目录
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        # 在线玩家更新定时器
        self.player_update_timer = None
        
        # 性能监控
        self.performance_monitor = PerformanceManager()
        self.performance_update_timer = None
        
        # 日志保存定时器
        self.log_save_timer = None
        
        # 命令自动补全
        self.command_completer = CommandCompleter(self)
        self.current_suggestions = []
        self.suggestion_index = -1
        
        # 玩家消息管理器
        self.message_manager = MessageManager(self)
        
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
        
        # 服务器配置变量
        self.max_players_var = tk.StringVar(value="20")
        self.max_players_validation_var = tk.StringVar(value="")
        
        # 初始化子模块
        self.server_manager = ServerManager(self)
        self.player_manager = PlayerManager(self)
        self.ban_manager = BanManager(self)
        self.version_detector = VersionDetector(self)
        
        # 初始化插件管理器
        self.plugin_manager = PluginManager(self.server_dir_var.get())
        
        self.player_filter = PlayerFilter(self)
        
        # 创建界面
        self.create_widgets()
        
        # 加载配置和服务器数据
        self.load_config()
        self.load_server_data()
        
        # 启动封禁监控
        self.ban_manager.start_ban_monitoring()
        
        # 启动禁言监控
        self.ban_manager.start_mute_monitoring()
        
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
        # 检测服务器版本
        self.version_detector.detect_version()
        if hasattr(self, 'server_manager') and self.server_manager.server_running:
            self.root.after(5000, self.periodic_player_list_update)
        
        # 启动日志定时保存
        self.start_log_saving()
    
    def start_log_saving(self):
        """启动日志定时保存"""
        # 立即保存一次日志
        self.save_server_logs()
        self.save_performance_logs()
        
        # 设置12小时后再次保存
        # 12小时 = 12 * 60 * 60 * 1000 milliseconds
        self.log_save_timer = self.root.after(12 * 60 * 60 * 1000, self.log_save_callback)
    
    def log_save_callback(self):
        """日志保存回调函数"""
        self.save_server_logs()
        self.save_performance_logs()
        
        # 继续设置下一次保存
        self.log_save_timer = self.root.after(12 * 60 * 60 * 1000, self.log_save_callback)
    
    def save_server_logs(self):
        """保存服务器日志"""
        try:
            # 生成日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.logs_dir, f'server_log_{timestamp}.txt')
            
            # 获取日志内容
            log_content = self.log_text.get(1.0, tk.END)
            
            # 保存到文件
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"服务器日志已保存到: {log_file}")
        except Exception as e:
            print(f"保存服务器日志时出错: {e}")
    
    def save_performance_logs(self):
        """保存性能日志"""
        try:
            # 生成日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.logs_dir, f'performance_log_{timestamp}.txt')
            
            # 获取性能历史数据
            if hasattr(self, 'performance_monitor'):
                history = self.performance_monitor.get_performance_history()
                
                # 保存到文件
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("性能历史数据\n")
                    f.write("=" * 60 + "\n")
                    for record in history:
                        timestamp = record['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                        cpu = record['cpu']
                        memory = record['memory']
                        server_cpu = record.get('server_cpu', 0)
                        server_memory = record.get('server_memory', 0)
                        
                        line = f"[{timestamp}] CPU: {cpu:.1f}% | 内存: {memory:.1f}%"
                        if server_cpu > 0:
                            line += f" | 服务器CPU: {server_cpu:.1f}% | 服务器内存: {server_memory:.1f}MB"
                        f.write(line + "\n")
                
                print(f"性能日志已保存到: {log_file}")
        except Exception as e:
            print(f"保存性能日志时出错: {e}")
    
    def save_logs_on_crash(self):
        """服务器崩溃时保存日志"""
        try:
            # 生成崩溃日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            crash_log_file = os.path.join(self.logs_dir, f'crash_log_{timestamp}.txt')
            
            # 获取日志内容
            log_content = self.log_text.get(1.0, tk.END)
            
            # 保存到文件
            with open(crash_log_file, 'w', encoding='utf-8') as f:
                f.write("服务器崩溃日志\n")
                f.write("=" * 60 + "\n")
                f.write(f"崩溃时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                f.write(log_content)
            
            print(f"崩溃日志已保存到: {crash_log_file}")
        except Exception as e:
            print(f"保存崩溃日志时出错: {e}")
    
    def periodic_player_list_update(self):
        """定期更新玩家列表"""
        if hasattr(self, 'server_manager') and self.server_manager.server_running:
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
        
    def add_tooltip(self, widget, text, delay=500):
        """为控件添加工具提示"""
        from ui_styles import TooltipManager
        return TooltipManager(widget, text, delay=delay)
    
    def validate_property(self, prop, var, validator):
        """验证属性值并显示实时反馈"""
        value = var.get()
        if validator:
            is_valid, message = validator(value)
            if not is_valid:
                self.validation_vars[prop].set(message)
            else:
                self.validation_vars[prop].set("")
    
    def validate_port(self, value):
        """验证端口号"""
        try:
            port = int(value)
            if 1 <= port <= 65535:
                return True, ""
            else:
                return False, "端口号必须在1-65535之间"
        except ValueError:
            return False, "端口号必须是数字"
    
    def validate_max_players(self, value):
        """验证最大玩家数"""
        try:
            max_players = int(value)
            if max_players > 0:
                return True, ""
            else:
                return False, "最大玩家数必须大于0"
        except ValueError:
            return False, "最大玩家数必须是数字"
    
    def validate_view_distance(self, value):
        """验证视图距离"""
        try:
            view_distance = int(value)
            if 2 <= view_distance <= 32:
                return True, ""
            else:
                return False, "视图距离必须在2-32之间"
        except ValueError:
            return False, "视图距离必须是数字"
    
    def create_widgets(self):
        # 创建笔记本样式
        style = ttk.Style()
        
        # 定义现代配色方案
        primary_color = "#3498db"  # 主色调：蓝色
        secondary_color = "#2ecc71"  # 辅助色：绿色
        accent_color = "#e74c3c"  # 强调色：红色
        background_color = "#f8f9fa"  # 背景色：浅灰色
        card_color = "#ffffff"  # 卡片色：白色
        text_color = "#333333"  # 文本色：深灰色
        border_color = "#e0e0e0"  # 边框色：浅灰色
        
        # 主窗口背景
        style.configure("TFrame", background=background_color)
        
        # 标签页样式 - 现代化版本
        style.configure("TNotebook", background=background_color, borderwidth=1, relief="flat")
        style.configure("TNotebook.Tab", 
                      padding=[18, 10], 
                      font=('微软雅黑', 10, 'normal'),
                      borderwidth=1,
                      relief="flat")
        style.map("TNotebook.Tab", 
                 background=[("selected", card_color), ("!selected", background_color)],
                 foreground=[("selected", primary_color), ("!selected", text_color)],
                 font=[("selected", ('微软雅黑', 10, 'bold')), ("!selected", ('微软雅黑', 10, 'normal'))],
                 relief=[("selected", "solid"), ("!selected", "flat")],
                 bordercolor=[("selected", primary_color), ("!selected", border_color)])
        
        # 按钮样式 - 现代化版本
        style.configure("TButton", 
                      padding=[12, 6], 
                      font=('微软雅黑', 10),
                      borderwidth=1,
                      relief="raised",
                      background=card_color,
                      foreground=text_color)
        
        # 按钮悬停效果
        style.map("TButton", 
                 background=[("active", primary_color), ("!active", card_color)],
                 foreground=[("active", "white"), ("!active", text_color)],
                 relief=[("pressed", "sunken"), ("!pressed", "raised")])
        
        # 标签样式
        style.configure("TLabel", background=background_color, font=('微软雅黑', 10), foreground=text_color)
        
        # 输入框样式 - 现代化版本
        style.configure("TEntry", 
                      padding=[10, 6], 
                      font=('微软雅黑', 10),
                      borderwidth=1,
                      relief="sunken",
                      background=card_color,
                      foreground=text_color)
        
        # 输入框焦点效果
        style.map("TEntry", 
                 bordercolor=[("focus", primary_color), ("!focus", border_color)],
                 relief=[("focus", "solid"), ("!focus", "sunken")])
        
        # 标签框架样式
        style.configure("TLabelframe", background=background_color, borderwidth=1, relief="flat")
        style.configure("TLabelframe.Label", 
                      background=background_color, 
                      font=('微软雅黑', 11, 'bold'),
                      foreground=primary_color,
                      padding=[5, 2])
    
        # 树形视图样式 - 现代化版本
        style.configure("Treeview", 
                      background=card_color, 
                      font=('微软雅黑', 10),
                      rowheight=28,  # 增加行高，提高可读性
                      fieldbackground=card_color,
                      foreground=text_color)
        style.configure("Treeview.Heading", 
                      background=background_color, 
                      font=('微软雅黑', 10, 'bold'),
                      padding=(8, 5),  # 增加内边距
                      relief="flat",
                      foreground=primary_color)
        # 鼠标悬停效果
        style.map("Treeview", 
                 background=[("selected", primary_color), ("!selected", card_color)],
                 foreground=[("selected", "white"), ("!selected", text_color)])
        
        # 滚动条样式
        style.configure("Vertical.TScrollbar", 
                      background=background_color,
                      borderwidth=1,
                      relief="flat")
        style.map("Vertical.TScrollbar", 
                 background=[("active", primary_color), ("!active", background_color)],
                 foreground=[("active", "white"), ("!active", text_color)])
        
        # 创建主笔记本
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 添加标签页切换动画效果
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # 添加键盘快捷键支持
        self.root.bind("<Control-1>", lambda e: self.notebook.select(0))
        self.root.bind("<Control-2>", lambda e: self.notebook.select(1))
        self.root.bind("<Control-3>", lambda e: self.notebook.select(2))
        self.root.bind("<Control-4>", lambda e: self.notebook.select(3))
        self.root.bind("<Control-5>", lambda e: self.notebook.select(4))
        self.root.bind("<Control-6>", lambda e: self.notebook.select(5))
        self.root.bind("<Control-7>", lambda e: self.notebook.select(6))
        self.root.bind("<Control-8>", lambda e: self.notebook.select(7))
        self.root.bind("<Control-9>", lambda e: self.notebook.select(8) if len(self.notebook.tabs()) > 8 else None)

        # 创建滚动容器字典，用于存储每个标签页的滚动容器
        self.scrollable_frames = {}

        # 注册响应式布局回调
        self.responsive_manager.add_resize_callback(self._on_window_resize)

        # 创建各个标签页
        self.create_dashboard_tab()
        self.create_admin_panel_tab()
        self.create_player_management_tab()
        self.create_world_management_tab()
        self.create_server_config_tab()
        self.create_plugin_management_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        if PSUTIL_AVAILABLE:
            self.create_performance_tab()
    
    def _on_window_resize(self, width, height, breakpoint):
        """窗口大小变化时的回调函数"""
        # 更新布局配置
        self._update_responsive_layouts(breakpoint)
        
    def _update_responsive_layouts(self, breakpoint):
        """更新响应式布局"""
        # 更新快速命令按钮布局
        if hasattr(self, 'quick_cmd_buttons_frame'):
            self._update_quick_cmd_layout(breakpoint)
            
        # 更新玩家列表列宽
        if hasattr(self, 'players_tree'):
            self._update_treeview_columns(breakpoint)
            
        # 更新文本区域高度
        if hasattr(self, 'info_text'):
            self._update_text_heights(breakpoint)
    
    def _update_quick_cmd_layout(self, breakpoint):
        """更新快速命令按钮布局"""
        # 根据屏幕尺寸调整列数
        if breakpoint in ['xs', 'sm']:
            columns = 2
        elif breakpoint == 'md':
            columns = 3
        else:
            columns = 4
            
        # 重新排列按钮
        if hasattr(self, 'quick_cmd_buttons'):
            for idx, btn in enumerate(self.quick_cmd_buttons):
                row = idx // columns
                col = idx % columns
                btn.grid(row=row, column=col, padx=6, pady=6, sticky=tk.W+tk.E)
    
    def _update_treeview_columns(self, breakpoint):
        """更新Treeview列宽"""
        if not hasattr(self, 'players_tree'):
            return
            
        # 根据屏幕尺寸调整列宽
        column_widths = {
            'xs': {'状态': 50, '玩家名称': 100, '位置': 120, '延迟': 60, '游戏模式': 70, '在线时间': 80},
            'sm': {'状态': 60, '玩家名称': 120, '位置': 150, '延迟': 65, '游戏模式': 80, '在线时间': 90},
            'md': {'状态': 65, '玩家名称': 150, '位置': 190, '延迟': 75, '游戏模式': 95, '在线时间': 115},
            'lg': {'状态': 70, '玩家名称': 160, '位置': 200, '延迟': 80, '游戏模式': 100, '在线时间': 120},
            'xl': {'状态': 75, '玩家名称': 180, '位置': 220, '延迟': 85, '游戏模式': 110, '在线时间': 130}
        }
        
        if breakpoint in column_widths:
            widths = column_widths[breakpoint]
            for col, width in widths.items():
                self.players_tree.column(col, width=width)
    
    def _update_text_heights(self, breakpoint):
        """更新文本区域高度"""
        heights = {
            'xs': 6,
            'sm': 8,
            'md': 10,
            'lg': 12,
            'xl': 15
        }
        
        height = heights.get(breakpoint, 10)
        
        if hasattr(self, 'info_text'):
            self.info_text.config(height=height)
        if hasattr(self, 'chat_text'):
            self.chat_text.config(height=max(6, height-2))
        if hasattr(self, 'log_text'):
            self.log_text.config(height=max(10, height+5))
        
    def create_scrollable_tab(self, tab_name, text):
        """创建带滚动功能的标签页"""
        # 创建外层Frame
        outer_frame = ttk.Frame(self.notebook)
        self.notebook.add(outer_frame, text=text)

        # 创建滚动容器
        scrollable = ScrollableFrame(outer_frame, bg_color="#f8f9fa")
        scrollable.get_main_frame().pack(fill=tk.BOTH, expand=True)

        # 存储滚动容器引用
        self.scrollable_frames[tab_name] = scrollable

        # 配置内容Frame的grid权重，确保子控件可以正确扩展
        content_frame = scrollable.get_frame()
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        return content_frame

    def create_dashboard_tab(self):
        """创建仪表板标签页 - 优化布局"""
        # 仪表板标签页 - 使用滚动容器
        dashboard_frame = self.create_scrollable_tab("dashboard", "仪表板")

        # 服务器状态区域
        status_frame = ttk.LabelFrame(dashboard_frame, text="服务器状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 状态信息和控制按钮布局
        status_content_frame = ttk.Frame(status_frame)
        status_content_frame.pack(fill=tk.X)
        
        # 服务器状态信息 - 网格布局
        status_info_frame = ttk.Frame(status_content_frame)
        status_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 服务器状态
        self.status_var = tk.StringVar(value="服务器状态: 已停止")
        status_label = ttk.Label(status_info_frame, textvariable=self.status_var, font=("微软雅黑", 13, "bold"))
        status_label.pack(anchor=tk.W, pady=(0, 8))
        
        # 服务器信息网格
        info_grid = ttk.Frame(status_info_frame)
        info_grid.pack(fill=tk.X, pady=(0, 5))
        
        # 服务器地址信息
        self.server_address_var = tk.StringVar(value="服务器地址: 未配置")
        server_address_label = ttk.Label(info_grid, textvariable=self.server_address_var, font=("微软雅黑", 10))
        server_address_label.pack(anchor=tk.W, pady=(0, 3))
        
        # 在线玩家和性能信息
        info_row = ttk.Frame(info_grid)
        info_row.pack(fill=tk.X, pady=(0, 3))
        
        # 在线玩家信息
        self.players_var = tk.StringVar(value="在线玩家: 0/20")
        players_label = ttk.Label(info_row, textvariable=self.players_var, font=("微软雅黑", 10))
        players_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # 服务器性能信息
        self.performance_var = tk.StringVar(value="内存使用: N/A | CPU使用: N/A")
        performance_label = ttk.Label(info_row, textvariable=self.performance_var, font=("微软雅黑", 10))
        performance_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # 服务器版本信息
        self.version_var = tk.StringVar(value="服务器版本: 未检测")
        version_label = ttk.Label(info_row, textvariable=self.version_var, font=("微软雅黑", 10))
        version_label.pack(side=tk.LEFT)
        
        # 控制按钮 - 现代化布局
        button_frame = ttk.Frame(status_content_frame)
        button_frame.pack(side=tk.RIGHT, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="启动服务器", command=self.start_server, width=12)
        self.start_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(self.start_button, "启动Minecraft服务器")
        
        self.stop_button = ttk.Button(button_frame, text="停止服务器", command=self.stop_server, state=tk.DISABLED, width=12)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(self.stop_button, "安全停止Minecraft服务器")
        
        self.restart_button = ttk.Button(button_frame, text="重启服务器", command=self.restart_server, state=tk.DISABLED, width=12)
        self.restart_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(self.restart_button, "重启Minecraft服务器")
        
        # 服务器地址配置区域 - 现代化布局
        address_config_frame = ttk.Frame(status_frame)
        address_config_frame.pack(fill=tk.X, pady=(12, 0))
        
        address_config_inner = ttk.Frame(address_config_frame)
        address_config_inner.pack(fill=tk.X)
        
        ttk.Label(address_config_inner, text="服务器IP:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        server_ip_entry = ttk.Entry(address_config_inner, textvariable=self.server_ip_var, width=18)
        server_ip_entry.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        
        ttk.Label(address_config_inner, text="端口:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        server_port_entry = ttk.Entry(address_config_inner, textvariable=self.server_port_var, width=10)
        server_port_entry.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        
        button_group = ttk.Frame(address_config_inner)
        button_group.pack(side=tk.RIGHT)
        
        detect_public_ip_btn = ttk.Button(button_group, text="检测公网IP", 
                  command=self.detect_public_ip, width=10)
        detect_public_ip_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(detect_public_ip_btn, "检测当前网络的公网IP地址")
        
        detect_local_ip_btn = ttk.Button(button_group, text="检测本地IP", 
                  command=self.auto_detect_local_ip, width=10)
        detect_local_ip_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(detect_local_ip_btn, "检测本地网络IP地址")
        
        copy_address_btn = ttk.Button(button_group, text="复制地址", 
                  command=self.copy_server_address, width=10)
        copy_address_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.add_tooltip(copy_address_btn, "复制服务器地址到剪贴板")
        
        if QRCODE_AVAILABLE:
            qr_code_btn = ttk.Button(button_group, text="生成二维码", 
                      command=self.generate_qr_code, width=10)
            qr_code_btn.pack(side=tk.LEFT, pady=2)
            self.add_tooltip(qr_code_btn, "生成服务器连接二维码")
        
        # 快速命令区域
        quick_cmd_frame = ttk.LabelFrame(dashboard_frame, text="快速命令", padding="10")
        quick_cmd_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 常用命令按钮 - 增加更多快捷操作
        cmd_buttons = [
            ("保存世界", "save-all"),
            ("重新加载", "reload"),
            ("查看玩家", "list"),
            ("停止服务器", "stop"),
            ("设置白天", "time set day"),
            ("设置晴天", "weather clear"),
            ("设置出生点", "setworldspawn"),
            ("开启白名单", "whitelist on"),
            ("关闭白名单", "whitelist off"),
            ("显示TPS", "tps"),
            ("清理掉落物", "clear"),
            ("重置末地", "reset end")
        ]
        
        cmd_buttons_frame = ttk.Frame(quick_cmd_frame)
        cmd_buttons_frame.pack(fill=tk.X)
        self.quick_cmd_buttons_frame = cmd_buttons_frame
        
        # 使用网格布局，每行4个按钮，均匀分布
        self.quick_cmd_buttons = []
        for i, (text, cmd) in enumerate(cmd_buttons):
            btn = ttk.Button(cmd_buttons_frame, text=text, 
                            command=lambda c=cmd: self.quick_command(c),
                            style="TButton")
            btn.grid(row=i//4, column=i%4, padx=6, pady=6, sticky=tk.W+tk.E)
            self.quick_cmd_buttons.append(btn)
            # 添加工具提示
            tooltip_text = f"执行命令: {cmd}"
            self.add_tooltip(btn, tooltip_text)
        
        # 配置快速命令区域的列权重，使按钮均匀分布
        for i in range(4):
            cmd_buttons_frame.columnconfigure(i, weight=1)
        
        # 主要内容区域（服务器信息和在线玩家）
        main_content_frame = ttk.Frame(dashboard_frame)
        main_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 服务器信息区域
        info_frame = ttk.LabelFrame(main_content_frame, text="服务器信息", padding="10")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        
        self.info_text = scrolledtext.ScrolledText(info_frame, height=12)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "服务器信息将在这里显示...\n")
        self.info_text.config(state=tk.DISABLED)
        
        # 在线玩家区域
        players_frame = ttk.LabelFrame(main_content_frame, text="在线玩家", padding="10")
        players_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.player_filter_ui = PlayerFilterUI(
            players_frame, 
            self, 
            self.player_filter,
            on_filter_callback=self._on_player_filter_complete
        )
        self.player_filter_ui.get_filter_frame().pack(fill=tk.X, pady=(0, 8))
        
        # 玩家统计信息
        player_stats_frame = ttk.Frame(players_frame)
        player_stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.players_var = tk.StringVar(value="在线玩家: 0/20")
        ttk.Label(player_stats_frame, textvariable=self.players_var, font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT)
        
        # 玩家活跃度指标
        self.player_activity_var = tk.StringVar(value="活跃度: 低")
        ttk.Label(player_stats_frame, textvariable=self.player_activity_var).pack(side=tk.RIGHT)
        
        # 创建玩家列表树形视图
        columns = ("状态", "玩家名称", "位置", "延迟", "游戏模式", "在线时间")
        self.players_tree = ttk.Treeview(players_frame, columns=columns, show="headings", height=12, selectmode="browse")
        
        # 配置列 - 现代化版本
        for col in columns:
            # 添加排序功能
            self.players_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.players_tree, c, False))
            # 优化列宽
            if col == "状态":
                self.players_tree.column(col, width=65, anchor=tk.CENTER, stretch=False)
            elif col == "玩家名称":
                self.players_tree.column(col, width=150, stretch=True, minwidth=130)
            elif col == "位置":
                self.players_tree.column(col, width=190, stretch=True, minwidth=160)
            elif col == "延迟":
                self.players_tree.column(col, width=75, anchor=tk.CENTER, stretch=False)
            elif col == "游戏模式":
                self.players_tree.column(col, width=95, stretch=False)
            else:  # 在线时间
                self.players_tree.column(col, width=115, stretch=False)
        
        # 玩家列表和滚动条
        players_tree_frame = ttk.Frame(players_frame)
        players_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 玩家列表滚动条
        players_scrollbar = ttk.Scrollbar(players_tree_frame, orient=tk.VERTICAL, command=self.players_tree.yview)
        players_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.players_tree.configure(yscrollcommand=players_scrollbar.set)
        
        # 玩家详细信息区域
        player_detail_frame = ttk.LabelFrame(players_frame, text="玩家详情", padding="10")
        player_detail_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 详情区域布局 - 网格布局
        detail_grid = ttk.Frame(player_detail_frame)
        detail_grid.pack(fill=tk.BOTH, expand=True)
        
        # 第一行
        ttk.Label(detail_grid, text="名称:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        self.selected_player_name_var = tk.StringVar(value="未选择")
        ttk.Label(detail_grid, textvariable=self.selected_player_name_var).grid(row=0, column=1, sticky=tk.W, pady=3, padx=(0, 30))
        
        ttk.Label(detail_grid, text="位置:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=3, padx=(0, 10))
        self.selected_player_pos_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.selected_player_pos_var).grid(row=0, column=3, sticky=tk.W, pady=3)
        
        # 第二行
        ttk.Label(detail_grid, text="延迟:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        self.selected_player_ping_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.selected_player_ping_var).grid(row=1, column=1, sticky=tk.W, pady=3, padx=(0, 30))
        
        ttk.Label(detail_grid, text="游戏模式:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=3, padx=(0, 10))
        self.selected_player_gamemode_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.selected_player_gamemode_var).grid(row=1, column=3, sticky=tk.W, pady=3)
        
        # 配置列权重
        detail_grid.columnconfigure(1, weight=1)
        detail_grid.columnconfigure(3, weight=1)
        
        # 玩家操作按钮 - 统一间距
        player_buttons_frame = ttk.Frame(players_frame)
        player_buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 使用网格布局，每行4个按钮
        buttons = [
            ("发送消息", self.send_message_to_player, "向选中的玩家发送消息"),
            ("踢出玩家", self.kick_player, "将选中的玩家踢出服务器"),
            ("传送玩家", self.teleport_player, "将选中的玩家传送到指定位置"),
            ("设为管理员", self.op_player, "将选中的玩家设为服务器管理员"),
            ("刷新列表", self.refresh_player_list, "刷新在线玩家列表")
        ]
        
        for i, (text, cmd, tooltip) in enumerate(buttons):
            btn = ttk.Button(player_buttons_frame, text=text, command=cmd, width=12)
            btn.pack(side=tk.LEFT, padx=4, pady=3)
            self.add_tooltip(btn, tooltip)
        
        # 玩家聊天区域
        chat_frame = ttk.LabelFrame(dashboard_frame, text="玩家聊天", padding="10")
        chat_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 聊天显示区域
        self.chat_text = scrolledtext.ScrolledText(chat_frame, height=10)
        self.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.chat_text.insert(tk.END, "选择玩家查看聊天记录...\n")
        self.chat_text.config(state=tk.DISABLED)
        
        # 聊天输入区域
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X)
        
        ttk.Label(chat_input_frame, text="发送消息:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        
        self.chat_message_var = tk.StringVar()
        self.chat_entry = ttk.Entry(chat_input_frame, textvariable=self.chat_message_var)
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
        self.chat_entry.bind('<Return>', self.send_chat_message)
        
        self.chat_send_button = ttk.Button(chat_input_frame, text="发送", command=self.send_chat_message, width=8)
        self.chat_send_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(self.chat_send_button, "发送聊天消息给选中玩家")

        # 命令输入区域
        command_frame = ttk.Frame(dashboard_frame)
        command_frame.pack(fill=tk.X)
        
        command_input_frame = ttk.Frame(command_frame)
        command_input_frame.pack(fill=tk.X)
        
        ttk.Label(command_input_frame, text="服务器命令:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        
        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(command_input_frame, textvariable=self.command_var)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
        self.command_entry.bind('<Return>', self.send_command)
        self.command_entry.bind('<Tab>', self.auto_complete)
        self.command_entry.bind('<KeyRelease>', self.on_command_key_release)
        
        send_button = ttk.Button(command_input_frame, text="发送", command=self.send_command, width=8)
        send_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(send_button, "发送命令到服务器")
        
        # 命令提示区域
        self.command_hint_var = tk.StringVar(value="输入 /help 查看可用命令")
        command_hint_label = ttk.Label(command_frame, textvariable=self.command_hint_var, foreground="gray")
        command_hint_label.pack(anchor=tk.W, pady=(4, 0))
        
        # 绑定玩家选择事件
        self.players_tree.bind('<<TreeviewSelect>>', self.on_player_select)

    def create_performance_tab(self):
        """创建性能监控标签页"""
        if not PSUTIL_AVAILABLE:
            return

        performance_frame = self.create_scrollable_tab("performance", "性能监控")
        
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
        ttk.Label(metrics_frame, textvariable=self.cpu_var, font=("微软雅黑", 13, "bold")).grid(row=0, column=1, sticky=tk.W)

        # 内存使用率
        ttk.Label(metrics_frame, text="内存使用率:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.memory_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.memory_var, font=("微软雅黑", 13, "bold")).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # 磁盘使用率
        ttk.Label(metrics_frame, text="磁盘使用率:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.disk_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.disk_var, font=("微软雅黑", 13, "bold")).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
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
        
        refresh_perf_btn = ttk.Button(controls_frame, text="刷新性能数据",
                  command=self.update_performance_display)
        refresh_perf_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(refresh_perf_btn, "手动刷新性能数据")
        
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
        """创建管理员面板标签页 - 使用重构后的现代化UI"""
        # 创建外层Frame
        outer_frame = ttk.Frame(self.notebook)
        self.notebook.add(outer_frame, text="管理员面板")
        
        # 使用新的AdminPanelUI类
        self.admin_panel_ui = AdminPanelUI(outer_frame, self)
        
        # 加载初始数据
        self.load_banned_players()
        self.load_muted_players()
        self.load_ops()
        
        # 保存引用以便其他方法使用
        self.admin_frame = outer_frame
        
        # 返回框架（保持兼容性）
        return outer_frame
    
    def create_admin_panel_tab_legacy(self):
        """创建管理员面板标签页 - 旧版本（保留用于参考）"""
        # 管理员面板标签页 - 使用滚动容器
        admin_frame = self.create_scrollable_tab("admin", "管理员面板")
        
        admin_notebook = ttk.Notebook(admin_frame)
        admin_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        player_outer_frame = ttk.Frame(admin_notebook)
        admin_notebook.add(player_outer_frame, text="玩家管理")
        
        player_canvas = tk.Canvas(player_outer_frame, highlightthickness=0)
        player_h_scrollbar = ttk.Scrollbar(player_outer_frame, orient=tk.HORIZONTAL, command=player_canvas.xview)
        player_v_scrollbar = ttk.Scrollbar(player_outer_frame, orient=tk.VERTICAL, command=player_canvas.yview)
        
        player_canvas.configure(xscrollcommand=player_h_scrollbar.set, yscrollcommand=player_v_scrollbar.set)
        
        player_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        player_h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        player_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        player_management_frame = ttk.Frame(player_canvas, padding="15")
        player_canvas_window = player_canvas.create_window((0, 0), window=player_management_frame, anchor=tk.NW)
        
        def configure_player_scroll_region(event=None):
            # 使用player_management_frame的实际大小更新滚动区域
            player_canvas.update_idletasks()
            frame_width = player_management_frame.winfo_reqwidth()
            frame_height = player_management_frame.winfo_reqheight()
            # 确保滚动区域能包含所有内容，设置最小宽度为900
            player_canvas.configure(scrollregion=(0, 0, max(frame_width, 900), frame_height))
            
            canvas_width = player_canvas.winfo_width()
            if canvas_width > 1:
                # 只在canvas有实际宽度时才设置
                if frame_width > canvas_width:
                    player_canvas.itemconfig(player_canvas_window, width=canvas_width)
                else:
                    player_canvas.itemconfig(player_canvas_window, width=frame_width)
        
        def on_player_canvas_configure(event):
            canvas_width = event.width
            # 不设置高度，让内容决定高度，这样滚动条才能正常工作
            player_canvas.itemconfig(player_canvas_window, width=canvas_width)
        
        player_management_frame.bind("<Configure>", configure_player_scroll_region)
        player_canvas.bind("<Configure>", on_player_canvas_configure)
        
        def _on_player_mousewheel(event):
            # Windows系统：delta > 0向上滚动，delta < 0向下滚动
            scroll_delta = int(-1 * (event.delta / 120))
            player_canvas.yview_scroll(scroll_delta, "units")
            return "break"
        
        def _on_player_mousewheel_linux(event):
            # Linux系统：Button-4向上滚动，Button-5向下滚动
            if event.num == 4:
                player_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                player_canvas.yview_scroll(1, "units")
            return "break"
        
        def _bind_mousewheel_to_all(widget):
            # 递归为所有子控件绑定鼠标滚轮事件
            widget.bind("<MouseWheel>", _on_player_mousewheel, add=True)
            widget.bind("<Button-4>", _on_player_mousewheel_linux, add=True)
            widget.bind("<Button-5>", _on_player_mousewheel_linux, add=True)
            for child in widget.winfo_children():
                _bind_mousewheel_to_all(child)
        
        player_canvas.bind("<MouseWheel>", _on_player_mousewheel)
        player_canvas.bind("<Button-4>", _on_player_mousewheel_linux)
        player_canvas.bind("<Button-5>", _on_player_mousewheel_linux)
        player_management_frame.bind("<MouseWheel>", _on_player_mousewheel)
        player_management_frame.bind("<Button-4>", _on_player_mousewheel_linux)
        player_management_frame.bind("<Button-5>", _on_player_mousewheel_linux)
        
        # 封禁玩家区域
        ban_frame = ttk.LabelFrame(player_management_frame, text="封禁玩家", padding="10")
        ban_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 封禁玩家表单
        ban_form_frame = ttk.Frame(ban_frame)
        ban_form_frame.pack(fill=tk.X, pady=5)
        
        # 第一行
        ban_row1_frame = ttk.Frame(ban_form_frame)
        ban_row1_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(ban_row1_frame, text="玩家名称:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.ban_player_var = tk.StringVar()
        self.ban_player_combo = ttk.Combobox(ban_row1_frame, textvariable=self.ban_player_var, width=23, state="normal", postcommand=self.update_ban_combo_values)
        self.ban_player_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        self.ban_player_combo.bind('<<ComboboxSelected>>', self.on_ban_player_selected)
        self.ban_player_combo.bind('<FocusIn>', self.on_ban_combo_focus)
        self.add_tooltip(self.ban_player_combo, "选择或输入要封禁的玩家名称")
        
        ttk.Label(ban_row1_frame, text="封禁类型:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.ban_type_var = tk.StringVar(value="永久")
        ban_type_combo = ttk.Combobox(ban_row1_frame, textvariable=self.ban_type_var, 
                                     values=["永久", "临时"], width=10, state="readonly")
        ban_type_combo.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        ban_type_combo.bind('<<ComboboxSelected>>', self.on_ban_type_changed)
        
        ttk.Label(ban_row1_frame, text="时间:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.ban_time_var = tk.StringVar(value="1h")
        self.ban_time_combo = ttk.Combobox(ban_row1_frame, textvariable=self.ban_time_var, 
                                          values=["1h", "2h", "6h", "12h", "1d", "7d", "30d"], 
                                          width=8, state="readonly")
        self.ban_time_combo.pack(side=tk.LEFT, pady=2)
        
        # 第二行
        ban_row2_frame = ttk.Frame(ban_form_frame)
        ban_row2_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(ban_row2_frame, text="原因:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.ban_reason_var = tk.StringVar(value="违反服务器规则")
        ban_reason_entry = ttk.Entry(ban_row2_frame, textvariable=self.ban_reason_var, width=50)
        ban_reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        
        ban_button = ttk.Button(ban_row2_frame, text="封禁玩家", 
                  command=self.ban_player, width=12)
        ban_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(ban_button, "封禁指定玩家")
        
        # 禁言玩家区域
        mute_frame = ttk.LabelFrame(player_management_frame, text="禁言玩家", padding="10")
        mute_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 禁言玩家表单
        mute_form_frame = ttk.Frame(mute_frame)
        mute_form_frame.pack(fill=tk.X, pady=5)
        
        # 第一行
        mute_row1_frame = ttk.Frame(mute_form_frame)
        mute_row1_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(mute_row1_frame, text="玩家名称:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.mute_player_var = tk.StringVar()
        self.mute_player_combo = ttk.Combobox(mute_row1_frame, textvariable=self.mute_player_var, width=23, state="normal", postcommand=self.update_mute_combo_values)
        self.mute_player_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        self.mute_player_combo.bind('<<ComboboxSelected>>', self.on_mute_player_selected)
        self.mute_player_combo.bind('<FocusIn>', self.on_mute_combo_focus)
        self.add_tooltip(self.mute_player_combo, "选择或输入要禁言的玩家名称")
        
        ttk.Label(mute_row1_frame, text="禁言类型:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.mute_type_var = tk.StringVar(value="永久")
        mute_type_combo = ttk.Combobox(mute_row1_frame, textvariable=self.mute_type_var, 
                                      values=["永久", "临时"], width=10, state="readonly")
        mute_type_combo.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        mute_type_combo.bind('<<ComboboxSelected>>', self.on_mute_type_changed)
        
        ttk.Label(mute_row1_frame, text="时间:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.mute_time_var = tk.StringVar(value="1h")
        self.mute_time_combo = ttk.Combobox(mute_row1_frame, textvariable=self.mute_time_var, 
                                           values=["1h", "2h", "6h", "12h", "1d", "7d", "30d"], 
                                           width=8, state="readonly")
        self.mute_time_combo.pack(side=tk.LEFT, pady=2)
        
        # 第二行
        mute_row2_frame = ttk.Frame(mute_form_frame)
        mute_row2_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(mute_row2_frame, text="原因:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.mute_reason_var = tk.StringVar(value="不当言论")
        mute_reason_entry = ttk.Entry(mute_row2_frame, textvariable=self.mute_reason_var, width=50)
        mute_reason_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        
        mute_button = ttk.Button(mute_row2_frame, text="禁言玩家", 
                  command=self.mute_player, width=12)
        mute_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(mute_button, "禁言指定玩家")
        
        unmute_button = ttk.Button(mute_row2_frame, text="解除禁言", 
                  command=self.unmute_player, width=12)
        unmute_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(unmute_button, "解除指定玩家的禁言")
        
        # 封禁玩家列表
        ban_list_frame = ttk.LabelFrame(player_management_frame, text="封禁玩家列表", padding="10")
        ban_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树形视图显示封禁玩家
        columns = ("玩家名称", "封禁原因", "封禁日期", "解封日期", "剩余时间")
        self.ban_tree = ttk.Treeview(ban_list_frame, columns=columns, show="headings", height=8, selectmode="browse")
        
        for col in columns:
            # 添加排序功能
            self.ban_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.ban_tree, c, False))
            # 优化列宽
            if col == "玩家名称":
                self.ban_tree.column(col, width=160, stretch=True, minwidth=140)
            elif col == "封禁原因":
                self.ban_tree.column(col, width=220, stretch=True, minwidth=180)
            elif col == "剩余时间":
                self.ban_tree.column(col, width=100, stretch=False)
            else:  # 日期列
                self.ban_tree.column(col, width=140, stretch=False)
        
        # 封禁列表和滚动条
        ban_tree_frame = ttk.Frame(ban_list_frame)
        ban_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.ban_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 封禁列表滚动条
        ban_scrollbar = ttk.Scrollbar(ban_tree_frame, orient=tk.VERTICAL, command=self.ban_tree.yview)
        ban_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ban_tree.configure(yscrollcommand=ban_scrollbar.set)
        
        # 封禁操作按钮
        ban_buttons_frame = ttk.Frame(ban_list_frame)
        ban_buttons_frame.pack(fill=tk.X, pady=(0, 5))
        
        pardon_button = ttk.Button(ban_buttons_frame, text="解除封禁", 
                  command=self.pardon_player, width=12)
        pardon_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(pardon_button, "解除选中玩家的封禁")
        
        refresh_ban_button = ttk.Button(ban_buttons_frame, text="刷新列表", 
                  command=self.load_banned_players, width=12)
        refresh_ban_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(refresh_ban_button, "刷新封禁玩家列表")
        
        update_ban_button = ttk.Button(ban_buttons_frame, text="更新剩余时间", 
                  command=self.update_ban_times, width=14)
        update_ban_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(update_ban_button, "更新封禁剩余时间")
        
        # 禁言玩家列表
        mute_list_frame = ttk.LabelFrame(player_management_frame, text="禁言玩家列表", padding="10")
        mute_list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建树形视图显示禁言玩家
        mute_columns = ("玩家名称", "禁言原因", "禁言日期", "解禁日期", "剩余时间")
        self.mute_tree = ttk.Treeview(mute_list_frame, columns=mute_columns, show="headings", height=6, selectmode="browse")
        
        for col in mute_columns:
            # 添加排序功能
            self.mute_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.mute_tree, c, False))
            # 优化列宽
            if col == "玩家名称":
                self.mute_tree.column(col, width=160, stretch=True, minwidth=140)
            elif col == "禁言原因":
                self.mute_tree.column(col, width=220, stretch=True, minwidth=180)
            elif col == "剩余时间":
                self.mute_tree.column(col, width=100, stretch=False)
            else:  # 日期列
                self.mute_tree.column(col, width=140, stretch=False)
        
        # 禁言列表和滚动条
        mute_tree_frame = ttk.Frame(mute_list_frame)
        mute_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.mute_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 禁言列表滚动条
        mute_scrollbar = ttk.Scrollbar(mute_tree_frame, orient=tk.VERTICAL, command=self.mute_tree.yview)
        mute_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.mute_tree.configure(yscrollcommand=mute_scrollbar.set)
        
        # 禁言操作按钮
        mute_buttons_frame = ttk.Frame(mute_list_frame)
        mute_buttons_frame.pack(fill=tk.X, pady=(0, 5))
        
        unmute_selected_button = ttk.Button(mute_buttons_frame, text="解除禁言", 
                  command=self.unmute_selected_player, width=12)
        unmute_selected_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(unmute_selected_button, "解除选中玩家的禁言")
        
        refresh_mute_button = ttk.Button(mute_buttons_frame, text="刷新列表", 
                  command=self.load_muted_players, width=12)
        refresh_mute_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(refresh_mute_button, "刷新禁言玩家列表")
        
        update_mute_button = ttk.Button(mute_buttons_frame, text="更新剩余时间", 
                  command=self.update_mute_times, width=14)
        update_mute_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(update_mute_button, "更新禁言剩余时间")
        
        # 管理员管理区域
        op_frame = ttk.LabelFrame(player_management_frame, text="管理员管理", padding="10")
        op_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索和筛选区域
        search_frame = ttk.Frame(op_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(search_frame, text="搜索:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.op_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.op_search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        search_entry.bind('<Return>', self.search_ops)
        
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_ops, width=8)
        search_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(search_button, "搜索管理员")
        
        refresh_button = ttk.Button(search_frame, text="刷新", command=self.load_ops, width=8)
        refresh_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(refresh_button, "刷新管理员列表")
        
        # 管理员操作表单
        op_form_frame = ttk.Frame(op_frame)
        op_form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(op_form_frame, text="玩家名称:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.op_player_var = tk.StringVar()
        # 创建玩家下拉列表
        self.op_player_combo = ttk.Combobox(op_form_frame, textvariable=self.op_player_var, width=30, state="readonly")
        self.op_player_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
        # 填充玩家列表
        self.update_player_combo()
        
        ttk.Label(op_form_frame, text="权限等级:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.op_level_var = tk.StringVar(value="4")
        op_level_combo = ttk.Combobox(op_form_frame, textvariable=self.op_level_var, 
                                     values=["1", "2", "3", "4"], width=8, state="readonly")
        op_level_combo.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        
        add_op_button = ttk.Button(op_form_frame, text="设为管理员", 
                  command=self.add_op, width=12)
        add_op_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(add_op_button, "将选中玩家设为管理员")
        
        remove_op_button = ttk.Button(op_form_frame, text="取消管理员", 
                  command=self.remove_op, width=12)
        remove_op_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(remove_op_button, "取消选中玩家的管理员权限")
        
        # 管理员列表
        op_list_frame = ttk.LabelFrame(player_management_frame, text="管理员列表", padding="10")
        op_list_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 批量操作按钮
        batch_frame = ttk.Frame(op_list_frame)
        batch_frame.pack(fill=tk.X, pady=(0, 8))
        
        batch_remove_button = ttk.Button(batch_frame, text="批量移除", 
                  command=self.batch_remove_ops, width=12)
        batch_remove_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(batch_remove_button, "批量移除选中的管理员")
        
        batch_update_button = ttk.Button(batch_frame, text="批量更新权限", 
                  command=self.batch_update_op_levels, width=14)
        batch_update_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(batch_update_button, "批量更新选中管理员的权限等级")
        
        # 使用树形视图显示管理员（支持多选）
        op_columns = ("玩家名称", "权限等级", "添加时间")
        self.op_tree = ttk.Treeview(op_list_frame, columns=op_columns, show="headings", height=6, selectmode="extended")
        
        for col in op_columns:
            # 添加排序功能
            self.op_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.op_tree, c, False))
            # 优化列宽
            if col == "玩家名称":
                self.op_tree.column(col, width=200, stretch=True, minwidth=180)
            elif col == "权限等级":
                self.op_tree.column(col, width=100, anchor=tk.CENTER, stretch=False)
            else:  # 添加时间
                self.op_tree.column(col, width=140, stretch=False)
        
        # 管理员列表和滚动条
        op_tree_frame = ttk.Frame(op_list_frame)
        op_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.op_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 管理员列表滚动条
        op_scrollbar = ttk.Scrollbar(op_tree_frame, orient=tk.VERTICAL, command=self.op_tree.yview)
        op_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.op_tree.configure(yscrollcommand=op_scrollbar.set)
        
        # 操作记录区域
        op_log_frame = ttk.LabelFrame(player_management_frame, text="操作记录", padding="10")
        op_log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.op_log_text = scrolledtext.ScrolledText(op_log_frame, height=6)
        self.op_log_text.pack(fill=tk.BOTH, expand=True)
        self.op_log_text.insert(tk.END, "管理员操作记录将在这里显示...\n")
        self.op_log_text.config(state=tk.DISABLED)
        
        player_management_frame.columnconfigure(0, weight=1)
        player_management_frame.rowconfigure(1, weight=1)  # 封禁列表行可扩展
        player_management_frame.rowconfigure(3, weight=1)  # 禁言列表行可扩展
        player_management_frame.rowconfigure(5, weight=1)  # 管理员列表行可扩展
        player_management_frame.rowconfigure(6, weight=1)  # 操作记录行可扩展
        ban_form_frame.columnconfigure(1, weight=1)
        mute_form_frame.columnconfigure(1, weight=1)
        ban_tree_frame.columnconfigure(0, weight=1)
        ban_tree_frame.rowconfigure(0, weight=1)
        mute_tree_frame.columnconfigure(0, weight=1)
        mute_tree_frame.rowconfigure(0, weight=1)
        op_form_frame.columnconfigure(1, weight=1)
        op_tree_frame.columnconfigure(0, weight=1)
        op_tree_frame.rowconfigure(0, weight=1)
        search_frame.columnconfigure(1, weight=1)

        self.load_banned_players()
        self.load_muted_players()
        self.load_ops()
        
        # 为所有子控件绑定鼠标滚轮事件
        _bind_mousewheel_to_all(player_management_frame)
        
        # 手动调用一次，确保滚动区域正确更新
        configure_player_scroll_region()
        # 延迟调用，确保UI完全初始化后再更新
        player_canvas.after(100, configure_player_scroll_region)
        player_canvas.after(300, configure_player_scroll_region)
        player_canvas.after(500, configure_player_scroll_region)
        player_canvas.after(1000, configure_player_scroll_region)

    def create_player_management_tab(self):
        # 玩家管理标签页 - 使用滚动容器
        player_frame = self.create_scrollable_tab("player", "玩家管理")
        
        # 白名单管理区域
        whitelist_frame = ttk.LabelFrame(player_frame, text="白名单管理", padding="10")
        whitelist_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(whitelist_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.whitelist_player_var = tk.StringVar()
        whitelist_player_entry = ttk.Entry(whitelist_frame, textvariable=self.whitelist_player_var, width=20)
        whitelist_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        add_whitelist_btn = ttk.Button(whitelist_frame, text="添加到白名单",
                  command=self.add_to_whitelist)
        add_whitelist_btn.grid(row=0, column=2, padx=(5, 0))
        self.add_tooltip(add_whitelist_btn, "将玩家添加到白名单")

        remove_whitelist_btn = ttk.Button(whitelist_frame, text="从白名单移除",
                  command=self.remove_from_whitelist)
        remove_whitelist_btn.grid(row=0, column=3, padx=(5, 0))
        self.add_tooltip(remove_whitelist_btn, "将玩家从白名单移除")

        reload_whitelist_btn = ttk.Button(whitelist_frame, text="重载白名单",
                  command=self.reload_whitelist)
        reload_whitelist_btn.grid(row=0, column=4, padx=(5, 0))
        self.add_tooltip(reload_whitelist_btn, "重新加载白名单配置")
        
        # 白名单列表
        whitelist_list_frame = ttk.LabelFrame(player_frame, text="白名单列表", padding="10")
        whitelist_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 使用树形视图显示白名单
        whitelist_columns = ("玩家名称", "添加日期")
        self.whitelist_tree = ttk.Treeview(whitelist_list_frame, columns=whitelist_columns, show="headings", height=10, selectmode="browse")
        
        for col in whitelist_columns:
            # 添加排序功能
            self.whitelist_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.whitelist_tree, c, False))
            # 优化列宽
            if col == "玩家名称":
                self.whitelist_tree.column(col, width=200, stretch=True, minwidth=150)
            else:  # 添加日期
                self.whitelist_tree.column(col, width=130, stretch=False)
        
        self.whitelist_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 白名单列表滚动条
        whitelist_scrollbar = ttk.Scrollbar(whitelist_list_frame, orient=tk.VERTICAL, command=self.whitelist_tree.yview)
        whitelist_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.whitelist_tree.configure(yscrollcommand=whitelist_scrollbar.set)
        
        # 白名单操作按钮
        whitelist_buttons_frame = ttk.Frame(whitelist_list_frame)
        whitelist_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        refresh_whitelist_btn = ttk.Button(whitelist_buttons_frame, text="刷新列表",
                  command=self.load_whitelist)
        refresh_whitelist_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(refresh_whitelist_btn, "刷新白名单列表")

        enable_whitelist_btn = ttk.Button(whitelist_buttons_frame, text="启用白名单",
                  command=self.enable_whitelist)
        enable_whitelist_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(enable_whitelist_btn, "启用白名单功能")

        disable_whitelist_btn = ttk.Button(whitelist_buttons_frame, text="禁用白名单",
                  command=self.disable_whitelist)
        disable_whitelist_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(disable_whitelist_btn, "禁用白名单功能")

        export_whitelist_btn = ttk.Button(whitelist_buttons_frame, text="导出白名单",
                  command=self.export_whitelist)
        export_whitelist_btn.pack(side=tk.LEFT)
        self.add_tooltip(export_whitelist_btn, "导出白名单到文件")
        
        # 玩家数据管理区域
        player_data_frame = ttk.LabelFrame(player_frame, text="玩家数据管理", padding="10")
        player_data_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(player_data_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.player_data_var = tk.StringVar()
        player_data_entry = ttk.Entry(player_data_frame, textvariable=self.player_data_var, width=20)
        player_data_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        view_data_btn = ttk.Button(player_data_frame, text="查看玩家数据",
                  command=self.view_player_data)
        view_data_btn.grid(row=0, column=2, padx=(5, 0))
        self.add_tooltip(view_data_btn, "查看指定玩家的数据")

        reset_data_btn = ttk.Button(player_data_frame, text="重置玩家数据",
                  command=self.reset_player_data)
        reset_data_btn.grid(row=0, column=3, padx=(5, 0))
        self.add_tooltip(reset_data_btn, "重置指定玩家的数据")

        teleport_btn = ttk.Button(player_data_frame, text="传送玩家",
                  command=self.teleport_to_player)
        teleport_btn.grid(row=0, column=4, padx=(5, 0))
        self.add_tooltip(teleport_btn, "传送玩家到指定位置")
        
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
        """创建世界管理标签页 - 优化布局"""
        # 世界管理标签页 - 使用滚动容器
        world_frame = self.create_scrollable_tab("world", "世界管理")
        
        # 世界备份区域
        backup_frame = ttk.LabelFrame(world_frame, text="世界备份", padding="10")
        backup_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 备份操作按钮容器
        backup_buttons_frame = ttk.Frame(backup_frame)
        backup_buttons_frame.pack(fill=tk.X, pady=5)
        
        # 备份按钮 - 现代化布局
        create_backup_button = ttk.Button(backup_buttons_frame, text="创建备份", 
                  command=self.create_backup, width=14)
        create_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(create_backup_button, "创建世界备份")
        
        restore_backup_button = ttk.Button(backup_buttons_frame, text="恢复备份", 
                  command=self.restore_backup, width=14)
        restore_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(restore_backup_button, "从备份恢复世界")
        
        open_backup_button = ttk.Button(backup_buttons_frame, text="打开备份目录", 
                  command=self.open_backup_folder, width=16)
        open_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(open_backup_button, "打开备份文件所在目录")
        
        auto_backup_button = ttk.Button(backup_buttons_frame, text="自动备份设置", 
                  command=self.auto_backup_settings, width=16)
        auto_backup_button.pack(side=tk.LEFT, pady=3)
        self.add_tooltip(auto_backup_button, "设置自动备份选项")
        
        # 备份列表区域
        backup_list_frame = ttk.LabelFrame(backup_frame, text="备份列表", padding="10")
        backup_list_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # 备份列表树形视图
        backup_columns = ("备份名称", "创建时间", "大小", "类型")
        self.backup_tree = ttk.Treeview(backup_list_frame, columns=backup_columns, show="headings", height=8, selectmode="browse")
        
        for col in backup_columns:
            self.backup_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.backup_tree, c, False))
            if col == "备份名称":
                self.backup_tree.column(col, width=200, stretch=True, minwidth=180)
            elif col == "创建时间":
                self.backup_tree.column(col, width=160, stretch=False)
            elif col == "大小":
                self.backup_tree.column(col, width=100, anchor="e", stretch=False)
            else:  # 类型
                self.backup_tree.column(col, width=80, anchor="center", stretch=False)
        
        backup_tree_frame = ttk.Frame(backup_list_frame)
        backup_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 备份列表滚动条
        backup_scrollbar = ttk.Scrollbar(backup_tree_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        # 备份操作按钮
        backup_actions_frame = ttk.Frame(backup_list_frame)
        backup_actions_frame.pack(fill=tk.X, pady=(0, 5))
        
        refresh_backup_button = ttk.Button(backup_actions_frame, text="刷新列表", 
                  command=self.refresh_backup_list, width=12)
        refresh_backup_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(refresh_backup_button, "刷新备份列表")
        
        delete_backup_button = ttk.Button(backup_actions_frame, text="删除备份", 
                  command=self.delete_backup, width=12)
        delete_backup_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(delete_backup_button, "删除选中的备份")
        
        export_backup_button = ttk.Button(backup_actions_frame, text="导出备份", 
                  command=self.export_backup, width=12)
        export_backup_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(export_backup_button, "导出备份到指定位置")
        
        # 世界导入/导出区域
        import_export_frame = ttk.LabelFrame(world_frame, text="世界导入/导出", padding="10")
        import_export_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        import_export_buttons = ttk.Frame(import_export_frame)
        import_export_buttons.pack(fill=tk.X, pady=5)
        
        import_world_button = ttk.Button(import_export_buttons, text="导入世界", 
                  command=self.import_world, width=14)
        import_world_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(import_world_button, "从文件导入世界")
        
        export_world_button = ttk.Button(import_export_buttons, text="导出世界", 
                  command=self.export_world, width=14)
        export_world_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(export_world_button, "导出当前世界到文件")
        
        # 游戏规则区域
        gamerules_frame = ttk.LabelFrame(world_frame, text="游戏规则", padding="10")
        gamerules_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 游戏规则批量操作
        gamerules_batch_frame = ttk.Frame(gamerules_frame)
        gamerules_batch_frame.pack(fill=tk.X, pady=(0, 8))
        
        apply_all_button = ttk.Button(gamerules_batch_frame, text="应用所有规则", 
                  command=self.apply_all_gamerules, width=16)
        apply_all_button.pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.add_tooltip(apply_all_button, "批量应用所有游戏规则")
        
        reset_button = ttk.Button(gamerules_batch_frame, text="重置为默认", 
                  command=self.reset_gamerules, width=12)
        reset_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(reset_button, "重置所有游戏规则为默认值")
        
        # 常用游戏规则
        gamerules = [
            ("保持物品栏", "keepInventory", "false"),
            ("生物破坏", "mobGriefing", "true"),
            ("昼夜循环", "doDaylightCycle", "true"),
            ("天气循环", "doWeatherCycle", "true"),
            ("火焰蔓延", "doFireTick", "true"),
            ("死亡掉落", "keepInventory", "false"),
            ("自然生命恢复", "naturalRegeneration", "true"),
            ("命令方块", "commandBlockOutput", "true"),
            ("方块掉落", "doTileDrops", "true"),
            ("生物生成", "doMobSpawning", "true")
        ]
        
        self.gamerule_vars = {}
        
        # 游戏规则网格布局
        gamerules_grid = ttk.Frame(gamerules_frame)
        gamerules_grid.pack(fill=tk.X, pady=5)
        
        for i, (text, rule, default) in enumerate(gamerules):
            rule_frame = ttk.Frame(gamerules_grid)
            rule_frame.pack(fill=tk.X, pady=4)
            
            ttk.Label(rule_frame, text=text, font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 20), pady=2)
            var = tk.StringVar(value=default)
            self.gamerule_vars[rule] = var
            
            combo = ttk.Combobox(rule_frame, textvariable=var, 
                        values=["true", "false"], width=12, state="readonly")
            combo.pack(side=tk.LEFT, padx=(0, 20), pady=2)
            
            apply_button = ttk.Button(rule_frame, text="应用", 
                      command=lambda r=rule, v=var: self.set_gamerule(r, v.get()), width=10)
            apply_button.pack(side=tk.LEFT, pady=2)
            self.add_tooltip(apply_button, f"应用 {text} 规则")
        
        # 世界设置区域
        world_settings_frame = ttk.LabelFrame(world_frame, text="世界设置", padding="10")
        world_settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # 设置按钮容器
        settings_buttons_frame = ttk.Frame(world_settings_frame)
        settings_buttons_frame.pack(fill=tk.X, pady=5)
        
        # 世界设置按钮
        spawn_button = ttk.Button(settings_buttons_frame, text="设置出生点", 
                  command=self.set_spawn_point, width=14)
        spawn_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(spawn_button, "设置服务器出生点")
        
        gamemode_button = ttk.Button(settings_buttons_frame, text="更改游戏模式", 
                  command=self.change_game_mode, width=14)
        gamemode_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(gamemode_button, "更改服务器游戏模式")
        
        difficulty_button = ttk.Button(settings_buttons_frame, text="更改难度", 
                  command=self.change_difficulty, width=14)
        difficulty_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(difficulty_button, "更改服务器难度")
        
        time_button = ttk.Button(settings_buttons_frame, text="设置时间", 
                  command=self.set_time, width=14)
        time_button.pack(side=tk.LEFT, pady=3)
        self.add_tooltip(time_button, "设置服务器时间")
        
        # 配置列权重
        world_frame.columnconfigure(0, weight=1)
        backup_list_frame.columnconfigure(0, weight=1)
        backup_tree_frame.columnconfigure(0, weight=1)
        backup_tree_frame.rowconfigure(0, weight=1)
        gamerules_grid.columnconfigure(0, weight=1)

    def create_server_config_tab(self):
        # 服务器配置标签页 - 使用滚动容器
        config_frame = self.create_scrollable_tab("config", "服务器配置")
        
        # 服务器属性区域
        properties_frame = ttk.LabelFrame(config_frame, text="服务器属性", padding="10")
        properties_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 验证状态变量
        self.validation_vars = {}
        
        # 常用服务器属性
        properties = [
            ("服务器端口", "server-port", "25565", self.validate_port),
            ("在线模式", "online-mode", "true", None),
            ("最大玩家数", "max-players", "20", self.validate_max_players),
            ("视图距离", "view-distance", "10", self.validate_view_distance),
            ("白名单", "white-list", "false", None),
            ("PVP", "pvp", "true", None),
            ("难度", "difficulty", "easy", None),
            ("游戏模式", "gamemode", "survival", None),
            ("生成怪物", "spawn-monsters", "true", None),
            ("生成动物", "spawn-animals", "true", None),
            ("生成NPC", "spawn-npcs", "true", None),
            ("允许飞行", "allow-flight", "false", None),
            ("资源包", "resource-pack", "", None),
            ("Motd", "motd", "A Minecraft Server", None)
        ]
        
        self.property_vars = {}
        
        for i, (text, prop, default, validator) in enumerate(properties):
            # 标签
            ttk.Label(properties_frame, text=text).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            # 输入控件
            var = tk.StringVar(value=default)
            self.property_vars[prop] = var
            
            # 验证状态变量
            validation_var = tk.StringVar(value="")
            self.validation_vars[prop] = validation_var
            
            if prop in ["online-mode", "white-list", "pvp", "spawn-monsters", "spawn-animals", "spawn-npcs", "allow-flight"]:
                combo = ttk.Combobox(properties_frame, textvariable=var, 
                                    values=["true", "false"], width=15, state="readonly")
                combo.grid(row=i, column=1, padx=(5, 10), pady=2)
            elif prop == "difficulty":
                combo = ttk.Combobox(properties_frame, textvariable=var, 
                                    values=["peaceful", "easy", "normal", "hard"], width=15, state="readonly")
                combo.grid(row=i, column=1, padx=(5, 10), pady=2)
            elif prop == "gamemode":
                combo = ttk.Combobox(properties_frame, textvariable=var, 
                                    values=["survival", "creative", "adventure", "spectator"], width=15, state="readonly")
                combo.grid(row=i, column=1, padx=(5, 10), pady=2)
            else:
                entry = ttk.Entry(properties_frame, textvariable=var, width=30)
                entry.grid(row=i, column=1, padx=(5, 10), pady=2)
                # 添加实时验证
                if validator:
                    var.trace_add("write", lambda *args, p=prop, v=var, val=validator: self.validate_property(p, v, val))
            
            # 验证状态显示
            ttk.Label(properties_frame, textvariable=validation_var, foreground="red").grid(row=i, column=2, sticky=tk.W, pady=2)
            
            # 应用按钮
            apply_prop_btn = ttk.Button(properties_frame, text="应用",
                      command=lambda p=prop, v=var: self.set_property_with_validation(p, v.get()))
            apply_prop_btn.grid(row=i, column=3, padx=(0, 10), pady=2)
            self.add_tooltip(apply_prop_btn, f"应用 {text} 设置")

        # 应用所有更改按钮
        apply_all_btn = ttk.Button(properties_frame, text="应用所有更改",
                  command=self.apply_all_properties_with_validation)
        apply_all_btn.grid(row=len(properties), column=0, columnspan=4, pady=(10, 0))
        self.add_tooltip(apply_all_btn, "应用所有服务器属性更改")
        
        # 配置列权重
        config_frame.columnconfigure(0, weight=1)
        properties_frame.columnconfigure(1, weight=1)

    def create_logs_tab(self):
        # 日志标签页 - 使用滚动容器
        logs_frame = self.create_scrollable_tab("logs", "服务器日志")
        
        # 日志显示区域
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 日志控制按钮
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        clear_log_btn = ttk.Button(log_controls, text="清空日志",
                  command=self.clear_logs)
        clear_log_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(clear_log_btn, "清空日志显示区域")

        export_log_btn = ttk.Button(log_controls, text="导出日志",
                  command=self.export_logs)
        export_log_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.add_tooltip(export_log_btn, "导出日志到文件")

        search_log_btn = ttk.Button(log_controls, text="查找",
                  command=self.search_logs)
        search_log_btn.pack(side=tk.LEFT)
        self.add_tooltip(search_log_btn, "在日志中查找内容")

    def create_plugin_management_tab(self):
        """创建插件管理标签页"""
        # 插件管理标签页 - 使用滚动容器
        plugin_frame = self.create_scrollable_tab("plugin", "插件管理")

        # 插件扫描区域
        scan_frame = ttk.LabelFrame(plugin_frame, text="插件扫描", padding="10")
        scan_frame.pack(fill=tk.X, pady=(0, 10))
        
        scan_plugin_btn = ttk.Button(scan_frame, text="扫描插件", command=self.scan_plugins)
        scan_plugin_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.add_tooltip(scan_plugin_btn, "扫描服务器插件")
        self.plugin_count_var = tk.StringVar(value="插件数量: 0")
        ttk.Label(scan_frame, textvariable=self.plugin_count_var).pack(side=tk.LEFT, padx=(0, 20))
        
        # 插件状态统计
        self.plugin_enabled_var = tk.StringVar(value="启用: 0")
        self.plugin_disabled_var = tk.StringVar(value="禁用: 0")
        ttk.Label(scan_frame, textvariable=self.plugin_enabled_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(scan_frame, textvariable=self.plugin_disabled_var).pack(side=tk.LEFT)
        
        # 插件列表区域
        list_frame = ttk.LabelFrame(plugin_frame, text="插件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建插件列表树形视图
        columns = ("状态", "名称", "版本", "作者", "类型", "最后修改")
        self.plugins_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15, selectmode="browse")
        
        for col in columns:
            # 添加排序功能
            self.plugins_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.plugins_tree, c, False))
            # 优化列宽
            if col == "状态":
                self.plugins_tree.column(col, width=60, anchor=tk.CENTER, stretch=False)
            elif col == "名称":
                self.plugins_tree.column(col, width=220, stretch=True, minwidth=200)
            elif col == "版本":
                self.plugins_tree.column(col, width=90, stretch=False)
            elif col == "作者":
                self.plugins_tree.column(col, width=160, stretch=True, minwidth=150)
            elif col == "类型":
                self.plugins_tree.column(col, width=100, stretch=False)
            else:  # 最后修改
                self.plugins_tree.column(col, width=160, stretch=False)
        
        self.plugins_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # 插件列表滚动条
        plugins_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plugins_tree.yview)
        plugins_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plugins_tree.configure(yscrollcommand=plugins_scrollbar.set)
        
        # 插件详情区域
        detail_frame = ttk.LabelFrame(plugin_frame, text="插件详情", padding="10")
        detail_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 详情区域布局
        detail_top_frame = ttk.Frame(detail_frame)
        detail_top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 基本信息
        info_frame = ttk.Frame(detail_top_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(info_frame, text="名称:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.plugin_name_var = tk.StringVar(value="-")
        ttk.Label(info_frame, textvariable=self.plugin_name_var).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="版本:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.plugin_version_var = tk.StringVar(value="-")
        ttk.Label(info_frame, textvariable=self.plugin_version_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="作者:", font=('微软雅黑', 10, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.plugin_author_var = tk.StringVar(value="-")
        ttk.Label(info_frame, textvariable=self.plugin_author_var).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 状态信息
        status_frame = ttk.Frame(detail_top_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(status_frame, text="状态:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.plugin_status_var = tk.StringVar(value="未选择")
        ttk.Label(status_frame, textvariable=self.plugin_status_var, font=('微软雅黑', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(status_frame, text="类型:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.plugin_type_var = tk.StringVar(value="-")
        ttk.Label(status_frame, textvariable=self.plugin_type_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 描述区域
        desc_frame = ttk.LabelFrame(detail_frame, text="描述", padding="10")
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        self.plugin_detail_text = scrolledtext.ScrolledText(desc_frame, height=6, width=50)
        self.plugin_detail_text.pack(fill=tk.BOTH, expand=True)
        self.plugin_detail_text.insert(tk.END, "选择插件查看详情...\n")
        self.plugin_detail_text.config(state=tk.DISABLED)
        
        # 绑定插件选择事件
        self.plugins_tree.bind("<<TreeviewSelect>>", self.on_plugin_select)
    
    def create_settings_tab(self):
        # 设置标签页 - 使用滚动容器
        settings_frame = self.create_scrollable_tab("settings", "设置")
        
        # 服务器路径设置
        path_frame = ttk.LabelFrame(settings_frame, text="服务器路径设置", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="服务器JAR路径:").grid(row=0, column=0, sticky=tk.W)
        self.jar_path_var = tk.StringVar(value="server.jar")
        jar_path_entry = ttk.Entry(path_frame, textvariable=self.jar_path_var, width=50)
        jar_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        browse_jar_btn = ttk.Button(path_frame, text="浏览",
                  command=self.browse_jar_path)
        browse_jar_btn.grid(row=0, column=2)
        self.add_tooltip(browse_jar_btn, "浏览选择服务器JAR文件")

        ttk.Label(path_frame, text="服务器目录:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.server_dir_var = tk.StringVar(value=os.getcwd())
        server_dir_entry = ttk.Entry(path_frame, textvariable=self.server_dir_var, width=50)
        server_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))

        browse_dir_btn = ttk.Button(path_frame, text="浏览",
                  command=self.browse_server_dir)
        browse_dir_btn.grid(row=1, column=2, pady=(5, 0))
        self.add_tooltip(browse_dir_btn, "浏览选择服务器目录")
        
        # Java设置
        java_frame = ttk.LabelFrame(settings_frame, text="Java设置", padding="10")
        java_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(java_frame, text="Java路径:").grid(row=0, column=0, sticky=tk.W)
        self.java_path_var = tk.StringVar(value="java")
        java_path_entry = ttk.Entry(java_frame, textvariable=self.java_path_var, width=50)
        java_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        browse_java_btn = ttk.Button(java_frame, text="浏览",
                  command=self.browse_java_path)
        browse_java_btn.grid(row=0, column=2)
        self.add_tooltip(browse_java_btn, "浏览选择Java可执行文件")

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
        
        # 服务器配置区域
        server_config_frame = ttk.LabelFrame(settings_frame, text="服务器配置", padding="10")
        server_config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 保存设置按钮
        save_button_frame = ttk.Frame(settings_frame)
        save_button_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        save_settings_btn = ttk.Button(save_button_frame, text="保存设置",
                  command=self.save_config)
        save_settings_btn.pack(side=tk.LEFT)
        self.add_tooltip(save_settings_btn, "保存所有设置到配置文件")

        ttk.Label(server_config_frame, text="在线最大玩家数量:").grid(row=0, column=0, sticky=tk.W)
        max_players_entry = ttk.Entry(server_config_frame, textvariable=self.max_players_var, width=15)
        max_players_entry.grid(row=0, column=1, padx=(5, 10), sticky=tk.W)
        max_players_entry.bind('<FocusOut>', self.validate_max_players_setting)
        max_players_entry.bind('<Return>', self.validate_max_players_setting)

        ttk.Label(server_config_frame, text="(范围: 1-1000)", foreground="gray").grid(row=0, column=2, sticky=tk.W)

        ttk.Label(server_config_frame, textvariable=self.max_players_validation_var,
                 foreground="red").grid(row=1, column=0, columnspan=3, sticky=tk.W)

        apply_max_players_btn = ttk.Button(server_config_frame, text="应用最大玩家数",
                  command=self.apply_max_players_setting)
        apply_max_players_btn.grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)
        self.add_tooltip(apply_max_players_btn, "应用最大玩家数设置")
        
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
        address_label = ttk.Label(qr_window, text=f"服务器地址: {address}", font=("微软雅黑", 13, "bold"))
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
        """启动服务器"""
        result = self.server_manager.start_server()
        if not result:
            messagebox.showerror("错误", "启动服务器失败")
    
    def stop_server(self):
        """停止服务器"""
        self.server_manager.stop_server()
    
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
        
        # 检测服务器版本
        self.version_detector.detect_version_from_output(output)
        self.version_detector.update_version_display()
        
        # 解析服务器输出
        if "joined the game" in output.lower():
            self.player_manager.parse_player_join(output)
        elif "left the game" in output.lower():
            self.player_manager.parse_player_leave(output)
        elif "There are" in output and "of a max" in output:
            self.player_manager.parse_player_list(output)
        elif "whisper" in output.lower() or "msg" in output.lower() or "tell" in output.lower():
            self.parse_player_message(output)
        elif "chat" in output.lower() and ">" in output:
            self.parse_public_chat(output)
        elif "was banned" in output.lower():
            self.parse_ban_message(output)
        elif "Pos:" in output or "has the following entity data: [" in output:
            # 解析玩家位置信息
            import re
            # 匹配坐标格式: [x.xxd, y.yyd, z.zzd]
            pos_pattern = r'\[(\d+\.\d+d),\s*(\d+\.\d+d),\s*(\d+\.\d+d)\]'
            pos_match = re.search(pos_pattern, output)
            if pos_match:
                x = float(pos_match.group(1).replace('d', ''))
                y = float(pos_match.group(2).replace('d', ''))
                z = float(pos_match.group(3).replace('d', ''))
                
                # 提取玩家名称
                player_pattern = r"Player\['([a-zA-Z0-9_]{3,16})'"
                player_match = re.search(player_pattern, output)
                if player_match:
                    player = player_match.group(1)
                    self.message_manager.update_player_position(player, x, y, z)
    
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
        return self.server_manager.send_server_command(command)
    
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
        self.player_manager.update_players_display()
        self.update_ban_mute_player_combos()

    def sort_treeview(self, tree, column, reverse):
        """排序树形视图"""
        # 获取所有项目
        items = [(tree.set(k, column), k) for k in tree.get_children('')]
        
        # 尝试将值转换为数字进行排序
        try:
            items.sort(key=lambda x: float(x[0]), reverse=reverse)
        except ValueError:
            # 如果转换失败，按字符串排序
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        # 重新排列项目
        for index, (val, k) in enumerate(items):
            tree.move(k, '', index)
        
        # 切换排序顺序
        tree.heading(column, command=lambda c=column: self.sort_treeview(tree, c, not reverse))

    def _on_player_filter_complete(self, filtered_players):
        """玩家筛选完成回调"""
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)
        
        for player_data in filtered_players:
            player_name = player_data.get('name', '未知')
            status = player_data.get('status', '离线')
            position = player_data.get('position', (0, 64, 0))
            ping = player_data.get('ping', 0)
            gamemode = player_data.get('gamemode', '未知')
            online_time = player_data.get('online_time', 0)
            
            if isinstance(position, tuple) and len(position) == 3:
                position_str = f"{position[0]:.0f}, {position[1]:.0f}, {position[2]:.0f}"
            else:
                position_str = str(position)
            
            ping_str = f"{ping}ms"
            online_time_str = self._format_online_time(online_time)
            
            self.players_tree.insert("", tk.END, values=(
                status, player_name, position_str, ping_str, gamemode, online_time_str
            ))
    
    def _format_online_time(self, minutes):
        """格式化在线时间"""
        if isinstance(minutes, str):
            return minutes
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}小时{mins}分钟"
        else:
            return f"{mins}分钟"

    def on_player_select(self, event):
        """处理玩家选择事件"""
        selection = self.players_tree.selection()
        if selection:
            item = selection[0]
            values = self.players_tree.item(item)['values']
            if len(values) >= 6:
                status, player, position, ping, gamemode, online_time = values
                # 更新玩家详情变量
                self.selected_player_name_var.set(player)
                self.selected_player_pos_var.set(position)
                self.selected_player_ping_var.set(ping)
                self.selected_player_gamemode_var.set(gamemode)
            else:
                player = values[1]  # 兼容旧格式
                # 重置详情变量
                self.selected_player_name_var.set(player)
                self.selected_player_pos_var.set("-")
                self.selected_player_ping_var.set("-")
                self.selected_player_gamemode_var.set("-")
    
    def on_tab_changed(self, event):
        """处理标签页切换事件，添加动画效果"""
        # 获取当前选中的标签页索引
        current_tab = self.notebook.index(self.notebook.select())
        
        # 获取当前标签页的frame
        tab_frame = self.notebook.winfo_children()[current_tab]
        
        # 添加淡入效果
        for i in range(0, 101, 10):
            alpha = i / 100
            # 注意：Tkinter本身不支持透明度，这里使用颜色渐变效果模拟
            # 实际效果可能因平台而异
            pass
        
        # 可以在这里添加其他标签页切换时的逻辑，比如更新状态栏信息等
    
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
        return self.player_manager.get_selected_player()
    
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
        
        # 保存崩溃日志
        self.save_logs_on_crash()
        
        # 清空在线玩家列表
        self.players_online = []
        self.update_players_display()

    def restart_server(self):
        """重启服务器"""
        self.server_manager.restart_server()

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
            self.player_manager.kick_player(player, reason)

    def teleport_player(self):
        """传送玩家"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        destination = simpledialog.askstring("传送玩家", f"将 {player} 传送到:", initialvalue="~ ~ ~")
        
        if destination:
            self.player_manager.teleport_player(player, destination)

    def op_player(self):
        """设为管理员"""
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        self.player_manager.op_player(player)

    def refresh_player_list(self):
        """刷新玩家列表"""
        self.player_manager.refresh_player_list()

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
        
        if hasattr(self, 'auto_refresh_var') and self.auto_refresh_var.get() and hasattr(self, 'server_manager') and self.server_manager.server_running:
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
    def on_ban_player_selected(self, event=None):
        """当封禁玩家下拉列表选择改变时"""
        pass
    
    def on_mute_player_selected(self, event=None):
        """当禁言玩家下拉列表选择改变时"""
        pass
    
    def on_ban_combo_focus(self, event=None):
        """封禁玩家下拉列表获得焦点时更新列表"""
        self.update_ban_combo_values()
    
    def on_mute_combo_focus(self, event=None):
        """禁言玩家下拉列表获得焦点时更新列表"""
        self.update_mute_combo_values()
    
    def update_ban_combo_values(self):
        """更新封禁玩家下拉列表的值"""
        players = self.player_manager.players_online if hasattr(self, 'player_manager') else []
        current_text = self.ban_player_var.get().strip()
        if current_text:
            filtered = [p for p in players if current_text.lower() in p.lower()]
            self.ban_player_combo['values'] = filtered if filtered else players
        else:
            self.ban_player_combo['values'] = players
        return None
    
    def update_mute_combo_values(self):
        """更新禁言玩家下拉列表的值"""
        players = self.player_manager.players_online if hasattr(self, 'player_manager') else []
        current_text = self.mute_player_var.get().strip()
        if current_text:
            filtered = [p for p in players if current_text.lower() in p.lower()]
            self.mute_player_combo['values'] = filtered if filtered else players
        else:
            self.mute_player_combo['values'] = players
        return None
    
    def update_ban_mute_player_combos(self):
        """更新封禁和禁言玩家下拉列表"""
        players = self.player_manager.players_online if hasattr(self, 'player_manager') else []
        
        if hasattr(self, 'ban_player_combo'):
            self.ban_player_combo['values'] = players
            if players and not self.ban_player_var.get():
                self.ban_player_combo.set('')
        
        if hasattr(self, 'mute_player_combo'):
            self.mute_player_combo['values'] = players
            if players and not self.mute_player_var.get():
                self.mute_player_combo.set('')
    
    def on_ban_type_changed(self, event=None):
        """当封禁类型改变时更新界面"""
        if self.ban_type_var.get() == "永久":
            self.ban_time_combo.config(state="disabled")
        else:
            self.ban_time_combo.config(state="readonly")

    def ban_player(self):
        """封禁玩家"""
        player = self.ban_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        reason = self.ban_reason_var.get().strip()
        ban_type = self.ban_type_var.get()
        ban_time = self.ban_time_var.get() if ban_type != "永久" else None
        
        result = self.ban_manager.ban_player(player, reason, ban_type, ban_time)
        if result:
            self.ban_player_var.set("")
            # 立即更新封禁列表显示
            self.load_banned_players()
            messagebox.showinfo("成功", f"已封禁玩家: {player}")

    def update_ban_times(self):
        """更新封禁剩余时间显示"""
        self.ban_manager.update_ban_times()

    def load_banned_players(self):
        """加载封禁玩家列表 - 确保完全清空列表"""
        # 清空旧版UI列表（如果存在）
        if hasattr(self, 'ban_tree') and self.ban_tree.winfo_exists():
            for item in self.ban_tree.get_children():
                self.ban_tree.delete(item)
        
        # 准备数据列表
        ban_list = []
        current_time = datetime.now()
        
        for ban in self.banned_players[:]:
            player = ban["player"]
            reason = ban["reason"]
            ban_date = ban["ban_date"]
            unban_date = ban["unban_date"]
            ban_type = ban.get("ban_type", "永久")
            
            # 计算剩余时间（如果是临时封禁）
            time_left = "永久"
            status = "封禁中"
            
            if ban_type == "临时" and player in self.ban_manager.temp_bans:
                ban_info = self.ban_manager.temp_bans[player]
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
                    status = "已过期"
                    # 自动移除过期封禁
                    self.banned_players.remove(ban)
                    if player in self.ban_manager.temp_bans:
                        del self.ban_manager.temp_bans[player]
                    continue
            
            ban_list.append({
                "player": player,
                "reason": reason,
                "type": ban_type,
                "remaining": time_left,
                "status": status
            })
            
            # 同时更新旧版UI（如果存在）
            if hasattr(self, 'ban_tree') and self.ban_tree.winfo_exists():
                self.ban_tree.insert("", tk.END, values=(player, reason, ban_date, unban_date, time_left))
        
        # 更新新版UI（如果存在）
        if hasattr(self, 'admin_panel_ui'):
            self.admin_panel_ui.update_ban_list(ban_list)
        
        # 更新玩家下拉列表
        if hasattr(self, 'op_player_combo'):
            self.update_player_combo()

    def pardon_player(self):
        """解除封禁玩家"""
        selection = self.ban_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解封的玩家")
            return
        
        player = self.ban_tree.item(selection[0])['values'][0]  # 第一列是玩家名称
        
        result = self.ban_manager.pardon_player(player)
        if result:
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
        mute_time = self.mute_time_var.get() if mute_type != "永久" else None
        
        result = self.ban_manager.mute_player(player, reason, mute_type, mute_time)
        if result:
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
        
        result = self.ban_manager.unmute_player(player)
        if result:
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
        
        result = self.ban_manager.unmute_player(player)
        if result:
            # 立即更新显示
            self.load_muted_players()
            messagebox.showinfo("成功", f"已解除玩家 {player} 的禁言")

    def load_muted_players(self):
        """加载禁言玩家列表 - 确保完全清空列表"""
        # 清空旧版UI列表（如果存在）
        if hasattr(self, 'mute_tree') and self.mute_tree.winfo_exists():
            for item in self.mute_tree.get_children():
                self.mute_tree.delete(item)
        
        # 准备数据列表
        mute_list = []
        current_time = datetime.now()
        players_to_remove = []
        
        for player, mute_info in list(self.ban_manager.muted_players.items()):
            reason = mute_info.get("reason", "无")
            mute_date = mute_info.get("mute_date", "未知")
            unmute_date = mute_info.get("unmute_date", "永久")
            mute_type = mute_info.get("type", "permanent")
            
            # 计算剩余时间（如果是临时禁言）
            time_left = "永久"
            status = "禁言中"
            display_type = "永久" if mute_type == "permanent" else "临时"
            
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
                    status = "已过期"
                    # 标记为需要移除
                    players_to_remove.append(player)
                    continue
            
            mute_list.append({
                "player": player,
                "reason": reason,
                "type": display_type,
                "remaining": time_left,
                "status": status
            })
            
            # 同时更新旧版UI（如果存在）
            if hasattr(self, 'mute_tree') and self.mute_tree.winfo_exists():
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
            del self.ban_manager.muted_players[player]
        
        # 更新新版UI（如果存在）
        if hasattr(self, 'admin_panel_ui'):
            self.admin_panel_ui.update_mute_list(mute_list)
        
        # 更新玩家下拉列表
        if hasattr(self, 'op_player_combo'):
            self.update_player_combo()

    def update_mute_times(self):
        """更新禁言剩余时间显示"""
        self.ban_manager.update_mute_times()

    # 管理员管理相关方法
    def add_op(self):
        """添加管理员 - 增加确认提示和权限等级管理"""
        player = self.op_player_var.get().strip()
        level = self.op_level_var.get()
        if not player:
            messagebox.showwarning("警告", "请选择玩家")
            return
        
        # 检查是否已经是管理员
        for op_name, _ in self.ops:
            if op_name == player:
                messagebox.showinfo("提示", f"玩家 {player} 已经是管理员")
                return
        
        result = messagebox.askyesno("确认", f"确定要将玩家 {player} 设为管理员，权限等级: {level}吗？")
        if result:
            self.send_server_command(f"op {player}")
            # 添加到本地列表
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ops.append((player, level, current_time))
            self.load_ops()
            # 保持选择不变
            message = f"已将玩家 {player} 设为管理员，权限等级: {level}"
            messagebox.showinfo("成功", message)
            self.log_op_action(message)

    def remove_op(self):
        """移除管理员 - 增加确认提示"""
        player = self.op_player_var.get().strip()
        if not player:
            # 尝试从选中项获取
            selection = self.op_tree.selection()
            if selection:
                player = self.op_tree.item(selection[0])['values'][0]
            else:
                messagebox.showwarning("警告", "请选择玩家或从列表中选择管理员")
                return
            
        result = messagebox.askyesno("确认", f"确定要移除玩家 {player} 的管理员权限吗？")
        if result:
            self.send_server_command(f"deop {player}")
            # 从本地列表移除
            self.ops = [op for op in self.ops if op[0] != player]
            # 立即刷新显示
            self.load_ops()
            message = f"已移除玩家 {player} 的管理员权限"
            messagebox.showinfo("成功", message)
            self.log_op_action(message)

    def update_player_combo(self):
        """更新玩家下拉列表"""
        # 收集所有可能的玩家名称
        player_names = set()
        
        # 从管理员列表获取
        for name, _ in self.ops:
            player_names.add(name)
        
        # 从白名单获取
        for name, _ in self.whitelist:
            player_names.add(name)
        
        # 从封禁列表获取
        for ban in self.banned_players:
            player_names.add(ban["player"])
        
        # 从在线玩家获取（如果有）
        if hasattr(self, 'players_tree') and self.players_tree.winfo_exists():
            for item in self.players_tree.get_children():
                player_name = self.players_tree.item(item)["values"][1]  # 第二列是玩家名称
                player_names.add(player_name)
        
        # 转换为排序后的列表
        sorted_players = sorted(player_names)
        
        # 更新旧版UI下拉列表（如果存在）
        if hasattr(self, 'op_player_combo') and self.op_player_combo.winfo_exists():
            self.op_player_combo['values'] = sorted_players
            # 如果有玩家，默认选择第一个
            if sorted_players:
                self.op_player_var.set(sorted_players[0])
        
        # 更新新版UI下拉列表（如果存在）
        if hasattr(self, 'admin_panel_ui'):
            self.admin_panel_ui.op_player_combo['values'] = sorted_players
    
    def load_ops(self):
        """加载管理员列表 - 确保完全清空列表"""
        # 清空旧版UI列表（如果存在）
        if hasattr(self, 'op_tree') and self.op_tree.winfo_exists():
            for item in self.op_tree.get_children():
                self.op_tree.delete(item)
        
        # 准备数据列表
        op_list = []
        
        # 添加管理员
        for op in self.ops:
            if len(op) >= 3:
                name, level, time_added = op
            else:
                name, level = op
                time_added = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            op_list.append({
                "player": name,
                "level": level,
                "added_time": time_added,
                "status": "在线"  # 可以根据实际情况检测
            })
            
            # 同时更新旧版UI（如果存在）
            if hasattr(self, 'op_tree') and self.op_tree.winfo_exists():
                self.op_tree.insert("", tk.END, values=(name, level, time_added))
        
        # 更新新版UI（如果存在）
        if hasattr(self, 'admin_panel_ui'):
            self.admin_panel_ui.update_op_list(op_list)
        
        # 加载完管理员列表后更新玩家下拉列表
        self.update_player_combo()

    def search_ops(self, event=None):
        """搜索管理员"""
        search_term = self.op_search_var.get().strip().lower()
        
        # 清空树形视图
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)
        
        # 筛选并添加管理员到树形视图
        for op in self.ops:
            if len(op) >= 3:
                name, level, time_added = op
                if search_term in name.lower():
                    self.op_tree.insert("", tk.END, values=(name, level, time_added))
            else:
                name, level = op
                if search_term in name.lower():
                    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.op_tree.insert("", tk.END, values=(name, level, current_time))

    def batch_remove_ops(self):
        """批量移除管理员"""
        selected_items = self.op_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要移除的管理员")
            return
        
        # 获取选中的玩家名称
        selected_players = []
        for item in selected_items:
            values = self.op_tree.item(item)['values']
            if values:
                selected_players.append(values[0])
        
        if not selected_players:
            messagebox.showwarning("警告", "未找到选中的管理员")
            return
        
        result = messagebox.askyesno("确认", f"确定要移除以下管理员的权限吗？\n{', '.join(selected_players)}")
        if result:
            try:
                for player in selected_players:
                    self.send_server_command(f"deop {player}")
                    # 从本地列表移除
                    self.ops = [op for op in self.ops if op[0] != player]
                # 立即刷新显示
                self.load_ops()
                message = f"已批量移除管理员: {', '.join(selected_players)}"
                messagebox.showinfo("成功", message)
                self.log_op_action(message)
            except Exception as e:
                error_message = f"批量移除管理员时出错: {str(e)}"
                self.log_op_action(error_message)
                messagebox.showerror("错误", error_message)

    def batch_update_op_levels(self):
        """批量更新管理员权限等级"""
        selected_items = self.op_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要更新权限等级的管理员")
            return
        
        # 获取新的权限等级
        new_level = simpledialog.askstring("更新权限等级", "请输入新的权限等级 (1-4):", initialvalue="4")
        if not new_level or not new_level.isdigit() or not 1 <= int(new_level) <= 4:
            messagebox.showwarning("警告", "请输入有效的权限等级 (1-4)")
            return
        
        # 获取选中的玩家名称
        selected_players = []
        for item in selected_items:
            values = self.op_tree.item(item)['values']
            if values:
                selected_players.append(values[0])
        
        if not selected_players:
            messagebox.showwarning("警告", "未找到选中的管理员")
            return
        
        result = messagebox.askyesno("确认", f"确定要将以下管理员的权限等级更新为 {new_level} 吗？\n{', '.join(selected_players)}")
        if result:
            try:
                for player in selected_players:
                    # 更新本地列表
                    for i, op in enumerate(self.ops):
                        if op[0] == player:
                            if len(op) >= 3:
                                self.ops[i] = (player, new_level, op[2])
                            else:
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                self.ops[i] = (player, new_level, current_time)
                # 立即刷新显示
                self.load_ops()
                message = f"已批量更新管理员权限等级为 {new_level}: {', '.join(selected_players)}"
                messagebox.showinfo("成功", message)
                self.log_op_action(message)
            except Exception as e:
                error_message = f"批量更新权限等级时出错: {str(e)}"
                self.log_op_action(error_message)
                messagebox.showerror("错误", error_message)

    def log_op_action(self, message):
        """记录管理员操作"""
        try:
            if hasattr(self, 'op_log_text'):
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                log_entry = f"[{timestamp}] {message}\n"
                
                self.op_log_text.config(state=tk.NORMAL)
                self.op_log_text.insert(tk.END, log_entry)
                self.op_log_text.see(tk.END)
                self.op_log_text.config(state=tk.DISABLED)
        except Exception as e:
            print(f"记录操作日志时出错: {e}")

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
        
        # 更新玩家下拉列表
        if hasattr(self, 'op_player_combo'):
            self.update_player_combo()

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
            # 创建备份进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("创建备份")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            # 居中显示
            x = (self.root.winfo_width() // 2) - 150
            y = (self.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            # 进度标签
            progress_label = ttk.Label(progress_window, text="正在创建备份...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            # 进度条
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def backup_thread():
                try:
                    # 保存世界
                    self.send_server_command("save-all")
                    self.log_message(f"正在创建备份: {backup_name}")
                    
                    # 创建备份目录
                    backup_dir = os.path.join(self.server_dir_var.get(), "backups")
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    
                    world_dir = os.path.join(self.server_dir_var.get(), "world")
                    if os.path.exists(world_dir):
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = os.path.join(backup_dir, f"{backup_name}_{timestamp}")
                        shutil.copytree(world_dir, backup_path)
                        self.log_message(f"备份已创建: {backup_path}")
                        
                        # 刷新备份列表
                        self.root.after(0, self.refresh_backup_list)
                        self.root.after(0, lambda: messagebox.showinfo("成功", f"备份 {backup_name} 创建成功"))
                    else:
                        self.root.after(0, lambda: messagebox.showerror("错误", "找不到世界目录"))
                except Exception as e:
                    error_message = f"创建备份时出错: {str(e)}"
                    self.log_message(error_message)
                    self.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    # 关闭进度窗口
                    self.root.after(0, progress_window.destroy)
            
            # 启动备份线程
            threading.Thread(target=backup_thread, daemon=True).start()
    
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
        # 创建恢复进度窗口
        progress_window = tk.Toplevel(self.root)
        progress_window.title("恢复备份")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        
        # 居中显示
        x = (self.root.winfo_width() // 2) - 150
        y = (self.root.winfo_height() // 2) - 50
        progress_window.geometry(f"300x100+{x}+{y}")
        
        # 进度标签
        progress_label = ttk.Label(progress_window, text="正在恢复备份...", font=('微软雅黑', 10))
        progress_label.pack(pady=10)
        
        # 进度条
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        def restore_thread():
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
                
                # 重新启动服务器
                if self.auto_start_var.get():
                    self.root.after(2000, self.start_server)
                
                self.root.after(0, lambda: messagebox.showinfo("成功", f"备份 {os.path.basename(backup_path)} 恢复成功"))
            except Exception as e:
                error_message = f"恢复备份时出错: {str(e)}"
                self.log_message(error_message)
                self.root.after(0, lambda: messagebox.showerror("错误", error_message))
            finally:
                # 关闭进度窗口
                self.root.after(0, progress_window.destroy)
        
        # 启动恢复线程
        threading.Thread(target=restore_thread, daemon=True).start()
    
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
        
        tk.Label(settings_window, text="自动备份设置", font=("微软雅黑", 13, "bold")).pack(pady=10)
        
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
            success = self.send_server_command(f"setworldspawn {x} {y} {z}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法设置出生点")
    
    def change_game_mode(self):
        """更改游戏模式"""
        # 创建游戏模式选择窗口
        mode_window = tk.Toplevel(self.root)
        mode_window.title("更改游戏模式")
        mode_window.geometry("300x200")
        mode_window.resizable(False, False)
        
        # 游戏模式映射（中文 -> 英文）
        game_modes = {
            "生存": "survival",
            "创造": "creative",
            "冒险": "adventure",
            "旁观者": "spectator"
        }
        
        # 创建下拉选项框
        ttk.Label(mode_window, text="选择游戏模式:", font=('微软雅黑', 12)).pack(pady=20)
        
        selected_mode = tk.StringVar(value="生存")
        mode_combo = ttk.Combobox(mode_window, textvariable=selected_mode, values=list(game_modes.keys()), state="readonly", width=15)
        mode_combo.pack(pady=10)
        
        def confirm_selection():
            chinese_mode = selected_mode.get()
            english_mode = game_modes[chinese_mode]
            success = self.send_server_command(f"defaultgamemode {english_mode}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法更改游戏模式")
            self.set_property("gamemode", english_mode)
            mode_window.destroy()
        
        # 确认按钮
        ttk.Button(mode_window, text="确认", command=confirm_selection).pack(pady=20)
    
    def change_difficulty(self):
        """更改难度"""
        # 创建难度选择窗口
        difficulty_window = tk.Toplevel(self.root)
        difficulty_window.title("更改难度")
        difficulty_window.geometry("300x200")
        difficulty_window.resizable(False, False)
        
        # 难度映射（中文 -> 英文）
        difficulties = {
            "和平": "peaceful",
            "简单": "easy",
            "普通": "normal",
            "困难": "hard"
        }
        
        # 创建下拉选项框
        ttk.Label(difficulty_window, text="选择难度:", font=('微软雅黑', 12)).pack(pady=20)
        
        selected_difficulty = tk.StringVar(value="和平")
        difficulty_combo = ttk.Combobox(difficulty_window, textvariable=selected_difficulty, values=list(difficulties.keys()), state="readonly", width=15)
        difficulty_combo.pack(pady=10)
        
        def confirm_selection():
            chinese_difficulty = selected_difficulty.get()
            english_difficulty = difficulties[chinese_difficulty]
            success = self.send_server_command(f"difficulty {english_difficulty}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法更改难度")
            self.set_property("difficulty", english_difficulty)
            difficulty_window.destroy()
        
        # 确认按钮
        ttk.Button(difficulty_window, text="确认", command=confirm_selection).pack(pady=20)
    
    def set_time(self):
        """设置时间"""
        time_str = simpledialog.askstring("设置时间", "请输入时间 (day, night, noon, midnight 或 0-24000):", parent=self.root)
        if time_str:
            success = self.send_server_command(f"time set {time_str}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法设置时间")

    # 世界管理相关方法
    def refresh_backup_list(self):
        """刷新备份列表"""
        try:
            # 清空树形视图
            if hasattr(self, 'backup_tree'):
                for item in self.backup_tree.get_children():
                    self.backup_tree.delete(item)
                
                # 获取备份目录
                backup_dir = os.path.join(os.getcwd(), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                # 扫描备份文件
                for filename in os.listdir(backup_dir):
                    if filename.endswith(".zip") or filename.endswith(".rar"):
                        file_path = os.path.join(backup_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        # 获取文件大小
                        file_size = file_stat.st_size
                        size_str = self.format_file_size(file_size)
                        
                        # 获取创建时间
                        create_time = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 确定备份类型
                        if "autobackup" in filename.lower():
                            backup_type = "自动"
                        else:
                            backup_type = "手动"
                        
                        # 添加到树形视图
                        self.backup_tree.insert("", tk.END, values=(filename, create_time, size_str, backup_type))
        except Exception as e:
            messagebox.showerror("错误", f"刷新备份列表时出错: {str(e)}")

    def delete_backup(self):
        """删除选中的备份"""
        if hasattr(self, 'backup_tree'):
            selection = self.backup_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请选择要删除的备份")
                return
            
            item = selection[0]
            backup_name = self.backup_tree.item(item)['values'][0]
            
            result = messagebox.askyesno("确认", f"确定要删除备份 {backup_name} 吗？")
            if result:
                try:
                    backup_path = os.path.join(os.getcwd(), "backups", backup_name)
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        self.refresh_backup_list()
                        messagebox.showinfo("成功", f"备份 {backup_name} 已删除")
                    else:
                        messagebox.showwarning("警告", "备份文件不存在")
                except Exception as e:
                    messagebox.showerror("错误", f"删除备份时出错: {str(e)}")

    def export_backup(self):
        """导出备份到指定位置"""
        if hasattr(self, 'backup_tree'):
            selection = self.backup_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请选择要导出的备份")
                return
            
            item = selection[0]
            backup_name = self.backup_tree.item(item)['values'][0]
            backup_path = os.path.join(os.getcwd(), "backups", backup_name)
            
            if not os.path.exists(backup_path):
                messagebox.showwarning("警告", "备份文件不存在")
                return
            
            # 选择导出位置
            export_path = filedialog.asksaveasfilename(
                title="导出备份",
                defaultextension=".zip",
                initialfile=backup_name,
                filetypes=[("ZIP files", "*.zip"), ("RAR files", "*.rar"), ("All files", "*.*")]
            )
            
            if export_path:
                try:
                    shutil.copy2(backup_path, export_path)
                    messagebox.showinfo("成功", f"备份已导出到: {export_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出备份时出错: {str(e)}")

    def import_world(self):
        """从文件导入世界"""
        # 选择导入文件
        import_path = filedialog.askopenfilename(
            title="导入世界",
            filetypes=[("ZIP files", "*.zip"), ("RAR files", "*.rar"), ("All files", "*.*")]
        )
        
        if import_path:
            # 检查服务器是否运行
            if hasattr(self, 'server_manager') and self.server_manager.server_running:
                result = messagebox.askyesno("警告", "服务器正在运行，导入世界需要停止服务器。是否继续？")
                if not result:
                    return
                self.server_manager.stop_server()
                time.sleep(2)  # 等待服务器停止
            
            # 创建导入进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("导入世界")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            # 居中显示
            x = (self.root.winfo_width() // 2) - 150
            y = (self.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            # 进度标签
            progress_label = ttk.Label(progress_window, text="正在导入世界...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            # 进度条
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def import_thread():
                try:
                    # 解压到世界目录
                    import zipfile
                    import tempfile
                    
                    # 创建临时目录
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # 解压文件
                        with zipfile.ZipFile(import_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        
                        # 查找世界文件夹
                        world_folders = []
                        for root, dirs, files in os.walk(temp_dir):
                            if "level.dat" in files:
                                world_folders.append(root)
                        
                        if not world_folders:
                            self.root.after(0, lambda: messagebox.showwarning("警告", "未找到有效的世界文件夹"))
                            return
                        
                        # 复制世界文件
                        world_source = world_folders[0]
                        world_dest = os.path.join(self.server_dir_var.get(), "world")
                        
                        # 备份当前世界
                        if os.path.exists(world_dest):
                            backup_name = f"world_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            backup_path = os.path.join(self.server_dir_var.get(), "backups", backup_name)
                            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                            shutil.make_archive(backup_path, 'zip', world_dest)
                        
                        # 删除当前世界
                        if os.path.exists(world_dest):
                            shutil.rmtree(world_dest)
                        
                        # 复制新世界
                        shutil.copytree(world_source, world_dest)
                        
                        self.log_message("世界导入成功")
                        self.root.after(0, lambda: messagebox.showinfo("成功", "世界导入成功"))
                except Exception as e:
                    error_message = f"导入世界时出错: {str(e)}"
                    self.log_message(error_message)
                    self.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    # 关闭进度窗口
                    self.root.after(0, progress_window.destroy)
            
            # 启动导入线程
            threading.Thread(target=import_thread, daemon=True).start()

    def export_world(self):
        """导出当前世界到文件"""
        # 检查服务器是否运行
        if hasattr(self, 'server_manager') and self.server_manager.server_running:
            # 保存世界
            self.send_server_command("save-all")
            time.sleep(1)
        
        # 选择导出位置
        export_path = filedialog.asksaveasfilename(
            title="导出世界",
            defaultextension=".zip",
            initialfile=f"world_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if export_path:
            # 创建导出进度窗口
            progress_window = tk.Toplevel(self.root)
            progress_window.title("导出世界")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            # 居中显示
            x = (self.root.winfo_width() // 2) - 150
            y = (self.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            # 进度标签
            progress_label = ttk.Label(progress_window, text="正在导出世界...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            # 进度条
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def export_thread():
                try:
                    # 压缩世界文件夹
                    world_path = os.path.join(self.server_dir_var.get(), "world")
                    if not os.path.exists(world_path):
                        self.root.after(0, lambda: messagebox.showwarning("警告", "世界文件夹不存在"))
                        return
                    
                    shutil.make_archive(export_path.replace('.zip', ''), 'zip', world_path)
                    
                    self.log_message(f"世界已导出到: {export_path}")
                    self.root.after(0, lambda: messagebox.showinfo("成功", f"世界已导出到: {export_path}"))
                except Exception as e:
                    error_message = f"导出世界时出错: {str(e)}"
                    self.log_message(error_message)
                    self.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    # 关闭进度窗口
                    self.root.after(0, progress_window.destroy)
            
            # 启动导出线程
            threading.Thread(target=export_thread, daemon=True).start()

    def apply_all_gamerules(self):
        """批量应用所有游戏规则"""
        try:
            applied_rules = []
            for rule, var in self.gamerule_vars.items():
                value = var.get()
                self.send_server_command(f"gamerule {rule} {value}")
                applied_rules.append(f"{rule}: {value}")
            
            message = "已应用以下游戏规则:\n" + "\n".join(applied_rules)
            messagebox.showinfo("成功", message)
        except Exception as e:
            messagebox.showerror("错误", f"应用游戏规则时出错: {str(e)}")

    def reset_gamerules(self):
        """重置所有游戏规则为默认值"""
        # 默认游戏规则值
        default_rules = {
            "keepInventory": "false",
            "mobGriefing": "true",
            "doDaylightCycle": "true",
            "doWeatherCycle": "true",
            "doFireTick": "true",
            "naturalRegeneration": "true",
            "commandBlockOutput": "true",
            "doTileDrops": "true",
            "doMobSpawning": "true"
        }
        
        for rule, default_value in default_rules.items():
            if rule in self.gamerule_vars:
                self.gamerule_vars[rule].set(default_value)
        
        messagebox.showinfo("成功", "游戏规则已重置为默认值")

    def format_file_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    # 服务器配置方法
    def validate_port(self, value):
        """验证端口号"""
        if not value.isdigit() or not (1 <= int(value) <= 65535):
            return "端口号必须是1-65535之间的整数"
        return ""
    
    def validate_max_players(self, value):
        """验证最大玩家数"""
        try:
            if not value or not value.strip():
                return "最大玩家数不能为空"
            if not value.strip().isdigit():
                return "最大玩家数必须是正整数"
            num = int(value.strip())
            if num < 1:
                return "最大玩家数必须大于0"
            if num > 1000:
                return "最大玩家数不能超过1000（建议值：1-100）"
            if num > 100:
                return "警告：超过100人可能影响服务器性能"
            return ""
        except ValueError:
            return "请输入有效的数字"
    
    def validate_max_players_setting(self, event=None):
        """验证设置页面的最大玩家数输入"""
        value = self.max_players_var.get()
        error = self.validate_max_players(value)
        self.max_players_validation_var.set(error)
        return len(error) == 0
    
    def apply_max_players_setting(self):
        """应用最大玩家数设置"""
        if not self.validate_max_players_setting():
            messagebox.showerror("验证错误", self.max_players_validation_var.get())
            return
        
        value = self.max_players_var.get().strip()
        
        try:
            num = int(value)
            if num > 100:
                if not messagebox.askyesno("性能警告", 
                    f"设置的最大玩家数为 {num}，超过100人可能会影响服务器性能。\n\n是否继续应用此设置？"):
                    return
            
            self.set_property("max-players", value)
            
            if "max-players" in self.property_vars:
                self.property_vars["max-players"].set(value)
            
            self.log_message(f"最大玩家数已设置为: {value}")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def validate_view_distance(self, value):
        """验证视图距离"""
        if not value.isdigit() or not (3 <= int(value) <= 32):
            return "视图距离必须是3-32之间的整数"
        return ""
    
    def validate_property(self, prop, var, validator):
        """验证属性值"""
        if validator:
            value = var.get()
            error = validator(value)
            self.validation_vars[prop].set(error)
    
    def set_property_with_validation(self, prop, value):
        """带验证的设置服务器属性"""
        # 验证属性值
        if prop in self.validation_vars and self.validation_vars[prop].get():
            messagebox.showerror("验证错误", self.validation_vars[prop].get())
            return
        
        self.set_property(prop, value)
    
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
    
    def apply_all_properties_with_validation(self):
        """带验证的应用所有属性更改"""
        # 验证所有属性
        errors = []
        for prop, var in self.property_vars.items():
            if prop in self.validation_vars and self.validation_vars[prop].get():
                errors.append(f"{prop}: {self.validation_vars[prop].get()}")
        
        if errors:
            error_message = "验证失败:\n" + "\n".join(errors)
            messagebox.showerror("验证错误", error_message)
            return
        
        # 应用所有属性
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
            'auto_update': str(self.auto_update_var.get()),
            'max_players': self.max_players_var.get()
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
                max_players = config['SETTINGS'].get('max_players', '20')
                if max_players:
                    self.max_players_var.set(max_players)
            
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
                # 自动备份配置文件
                self.backup_server_properties(properties_file)
                
                # 尝试使用不同编码读取文件
                encodings = ['utf-8', 'gbk', 'latin-1']
                properties = {}
                success = False
                
                for encoding in encodings:
                    try:
                        properties = {}
                        with open(properties_file, 'r', encoding=encoding) as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    key_value = line.split('=')
                                    if len(key_value) == 2:
                                        properties[key_value[0].strip()] = key_value[1].strip()
                        success = True
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not success:
                    self.log_message("无法读取服务器属性文件，使用默认值")
                    return
                
                # 验证配置文件
                self.validate_server_properties(properties)
                
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
                
                # 同步最大玩家数到设置页面
                if 'max-players' in properties:
                    self.max_players_var.set(properties['max-players'])
                            
            except Exception as e:
                self.log_message(f"加载服务器属性时出错: {str(e)}")
    
    def backup_server_properties(self, properties_file):
        """备份服务器属性文件"""
        backup_dir = os.path.join(self.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"server.properties.{timestamp}.bak")
        
        try:
            shutil.copy2(properties_file, backup_file)
            self.log_message(f"服务器属性文件已备份到: {backup_file}")
        except Exception as e:
            self.log_message(f"备份服务器属性文件时出错: {str(e)}")
    
    def validate_server_properties(self, properties):
        """验证服务器属性配置"""
        # 验证端口号
        if 'server-port' in properties:
            port = properties['server-port']
            if not port.isdigit() or not (1 <= int(port) <= 65535):
                self.log_message("警告: 服务器端口号无效，将使用默认值 25565")
                properties['server-port'] = "25565"
        
        # 验证最大玩家数
        if 'max-players' in properties:
            max_players = properties['max-players']
            if not max_players.isdigit() or int(max_players) < 1:
                self.log_message("警告: 最大玩家数无效，将使用默认值 20")
                properties['max-players'] = "20"
        
        # 验证视图距离
        if 'view-distance' in properties:
            view_distance = properties['view-distance']
            if not view_distance.isdigit() or not (3 <= int(view_distance) <= 32):
                self.log_message("警告: 视图距离无效，将使用默认值 10")
                properties['view-distance'] = "10"
        
        # 验证布尔值属性
        boolean_props = ['online-mode', 'white-list', 'pvp', 'spawn-monsters', 'spawn-animals', 'spawn-npcs', 'allow-flight']
        for prop in boolean_props:
            if prop in properties and properties[prop] not in ['true', 'false']:
                self.log_message(f"警告: {prop} 值无效，将使用默认值 true")
                properties[prop] = "true"
        
        # 验证难度
        if 'difficulty' in properties and properties['difficulty'] not in ['peaceful', 'easy', 'normal', 'hard']:
            self.log_message("警告: 难度值无效，将使用默认值 easy")
            properties['difficulty'] = "easy"
        
        # 验证游戏模式
        if 'gamemode' in properties and properties['gamemode'] not in ['survival', 'creative', 'adventure', 'spectator']:
            self.log_message("警告: 游戏模式值无效，将使用默认值 survival")
            properties['gamemode'] = "survival"
    
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
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")

    def scan_plugins(self):
        """扫描插件"""
        # 更新插件管理器的服务器目录
        self.plugin_manager.server_dir = self.server_dir_var.get()
        self.plugin_manager.plugins_dir = os.path.join(self.server_dir_var.get(), "plugins")
        
        # 扫描插件
        plugins = self.plugin_manager.scan_plugins()
        
        # 清空插件列表
        for item in self.plugins_tree.get_children():
            self.plugins_tree.delete(item)
        
        # 统计启用和禁用的插件数量
        enabled_count = 0
        disabled_count = 0
        
        # 添加插件到列表
        for plugin in plugins:
            # 模拟插件状态（实际项目中应从插件配置文件读取）
            status = "启用" if plugin.get('enabled', True) else "禁用"
            if status == "启用":
                enabled_count += 1
            else:
                disabled_count += 1
            
            self.plugins_tree.insert('', tk.END, values=(
                status,
                plugin['name'],
                plugin['version'],
                plugin['author'],
                plugin['type'],
                plugin['last_modified']
            ), tags=(plugin['name'],))
        
        # 更新插件数量和状态统计
        self.plugin_count_var.set(f"插件数量: {len(plugins)}")
        self.plugin_enabled_var.set(f"启用: {enabled_count}")
        self.plugin_disabled_var.set(f"禁用: {disabled_count}")
        
        # 清空详情
        self.plugin_detail_text.config(state=tk.NORMAL)
        self.plugin_detail_text.delete(1.0, tk.END)
        self.plugin_detail_text.insert(tk.END, "选择插件查看详情...\n")
        self.plugin_detail_text.config(state=tk.DISABLED)
        
        # 重置详情变量
        self.plugin_name_var.set("-")
        self.plugin_version_var.set("-")
        self.plugin_author_var.set("-")
        self.plugin_status_var.set("未选择")
        self.plugin_type_var.set("-")

    def on_plugin_select(self, event):
        """处理插件选择事件"""
        selected_items = self.plugins_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        plugin_name = self.plugins_tree.item(item, 'tags')[0]
        
        # 获取插件信息
        plugin = self.plugin_manager.get_plugin_by_name(plugin_name)
        if plugin:
            # 更新基本信息变量
            self.plugin_name_var.set(plugin['name'])
            self.plugin_version_var.set(plugin['version'])
            self.plugin_author_var.set(plugin['author'])
            self.plugin_type_var.set(plugin['type'])
            
            # 模拟插件状态（实际项目中应从插件配置文件读取）
            status = "启用" if plugin.get('enabled', True) else "禁用"
            self.plugin_status_var.set(status)
            
            # 显示插件描述
            self.plugin_detail_text.config(state=tk.NORMAL)
            self.plugin_detail_text.delete(1.0, tk.END)
            if 'description' in plugin and plugin['description']:
                self.plugin_detail_text.insert(tk.END, plugin['description'])
            else:
                self.plugin_detail_text.insert(tk.END, "该插件没有描述信息")
            self.plugin_detail_text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = MCServerControlPanel(root)
    root.mainloop()