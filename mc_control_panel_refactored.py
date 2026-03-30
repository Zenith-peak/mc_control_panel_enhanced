import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import threading
import time
import os
import json
import webbrowser
import shutil
from datetime import datetime, timedelta
import re
import sys
import urllib.request
import socket

from server_manager import ServerManager
from player_manager import PlayerManager
from ban_manager import BanManager
from performance_manager import PerformanceManager
from message_manager import MessageManager
from command_completer import CommandCompleter
from plugin_manager import PluginManager
from version_detector import VersionDetector
from player_filter import PlayerFilter, PlayerFilterUI

from ui_styles import UIStyles, TooltipManager
from ui_tabs import DashboardTab, PerformanceTab, LogsTab, SettingsTab, ServerConfigTab
from world_manager import WorldManager
from whitelist_manager import WhitelistManager
from config_manager import ConfigManager
from server_properties_manager import ServerPropertiesManager
from log_manager import LogManager

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

try:
    import qrcode
    from PIL import Image, ImageTk
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("qrcode或PIL未安装，二维码功能将被禁用")


class MCServerControlPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft 服务器控制面板 V0.1.5-beta3")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleCP(65001)
                kernel32.SetConsoleOutputCP(65001)
            except:
                pass
        
        self.banned_players = []
        self.ops = []
        self.whitelist = []
        self.server_properties = {}
        
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
        
        self.player_update_timer = None
        self.performance_monitor = PerformanceManager()
        self.performance_update_timer = None
        self.log_save_timer = None
        
        self.command_completer = CommandCompleter(self)
        self.current_suggestions = []
        self.suggestion_index = -1
        
        self.message_manager = MessageManager(self)
        
        self.server_ip_var = tk.StringVar()
        self.server_port_var = tk.StringVar(value="25565")
        self.server_address_var = tk.StringVar(value="服务器地址: 未配置")
        
        self.jar_path_var = tk.StringVar(value="server.jar")
        self.server_dir_var = tk.StringVar(value=os.getcwd())
        self.java_path_var = tk.StringVar(value="java")
        self.min_mem_var = tk.StringVar(value="1G")
        self.max_mem_var = tk.StringVar(value="2G")
        
        self.auto_start_var = tk.BooleanVar(value=False)
        self.auto_backup_var = tk.BooleanVar(value=False)
        self.auto_update_var = tk.BooleanVar(value=False)
        
        self.max_players_var = tk.StringVar(value="20")
        self.max_players_validation_var = tk.StringVar(value="")
        
        self.server_manager = ServerManager(self)
        self.player_manager = PlayerManager(self)
        self.ban_manager = BanManager(self)
        self.version_detector = VersionDetector(self)
        self.plugin_manager = PluginManager(self.server_dir_var.get())
        self.player_filter = PlayerFilter(self)
        
        self.ui_styles = UIStyles()
        self.tooltip_manager = TooltipManager()
        self.world_manager = WorldManager(self)
        self.whitelist_manager = WhitelistManager(self)
        self.config_manager = ConfigManager(self)
        self.server_properties_manager = ServerPropertiesManager(self)
        self.log_manager = LogManager(self)
        
        self.add_tooltip = self.tooltip_manager.add_tooltip
        
        self.create_widgets()
        
        self.config_manager.load_config()
        self.load_server_data()
        
        self.ban_manager.start_ban_monitoring()
        self.ban_manager.start_mute_monitoring()
        
        self.update_server_address_display()
        self.auto_detect_local_ip()
        self.start_periodic_updates()
    
    def create_widgets(self):
        self.ui_styles.apply_styles()
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        self.root.bind("<Control-1>", lambda e: self.notebook.select(0))
        self.root.bind("<Control-2>", lambda e: self.notebook.select(1))
        self.root.bind("<Control-3>", lambda e: self.notebook.select(2))
        self.root.bind("<Control-4>", lambda e: self.notebook.select(3))
        self.root.bind("<Control-5>", lambda e: self.notebook.select(4))
        self.root.bind("<Control-6>", lambda e: self.notebook.select(5))
        self.root.bind("<Control-7>", lambda e: self.notebook.select(6))
        self.root.bind("<Control-8>", lambda e: self.notebook.select(7))
        self.root.bind("<Control-9>", lambda e: self.notebook.select(8) if len(self.notebook.tabs()) > 8 else None)
        
        dashboard_tab = DashboardTab(self.notebook, self)
        self.notebook.add(dashboard_tab.create(), text="仪表板")
        
        self.create_admin_panel_tab()
        self.create_player_management_tab()
        self.create_world_management_tab()
        
        server_config_tab = ServerConfigTab(self.notebook, self)
        self.notebook.add(server_config_tab.create(), text="服务器配置")
        
        self.create_plugin_management_tab()
        
        logs_tab = LogsTab(self.notebook, self)
        self.notebook.add(logs_tab.create(), text="服务器日志")
        
        settings_tab = SettingsTab(self.notebook, self)
        self.notebook.add(settings_tab.create(), text="设置")
        
        if PSUTIL_AVAILABLE:
            performance_tab = PerformanceTab(self.notebook, self)
            self.notebook.add(performance_tab.create(), text="性能监控")
    
    def create_admin_panel_tab(self):
        admin_frame = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(admin_frame, text="管理员面板")
        
        admin_notebook = ttk.Notebook(admin_frame)
        admin_notebook.pack(fill=tk.BOTH, expand=True)
        
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
            player_canvas.configure(scrollregion=(0, 0, frame_width, frame_height))
            
            canvas_width = player_canvas.winfo_width()
            if frame_width > canvas_width:
                player_canvas.itemconfig(player_canvas_window, width=canvas_width)
            else:
                player_canvas.itemconfig(player_canvas_window, width=canvas_width)
        
        def on_player_canvas_configure(event):
            canvas_width = event.width
            player_canvas.itemconfig(player_canvas_window, width=canvas_width)
        
        player_management_frame.bind("<Configure>", configure_player_scroll_region)
        player_canvas.bind("<Configure>", on_player_canvas_configure)
        
        def _on_player_mousewheel(event):
            player_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        player_canvas.bind("<MouseWheel>", _on_player_mousewheel)
        
        self._create_ban_section(player_management_frame)
        self._create_mute_section(player_management_frame)
        self._create_op_section(player_management_frame)
        
        player_management_frame.columnconfigure(0, weight=1)
        player_management_frame.rowconfigure(1, weight=1)  # 封禁列表行可扩展
        player_management_frame.rowconfigure(3, weight=1)  # 禁言列表行可扩展
        player_management_frame.rowconfigure(5, weight=1)  # 管理员列表行可扩展
        
        self.load_banned_players()
        self.load_muted_players()
        self.load_ops()
    
    def _create_ban_section(self, parent):
        ban_frame = ttk.LabelFrame(parent, text="封禁玩家", padding="12")
        ban_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        ban_form_frame = ttk.Frame(ban_frame)
        ban_form_frame.pack(fill=tk.X, pady=5)
        
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
        
        ban_list_frame = ttk.LabelFrame(parent, text="封禁玩家列表", padding="12")
        ban_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        
        columns = ("玩家名称", "封禁原因", "封禁日期", "解封日期", "剩余时间")
        self.ban_tree = ttk.Treeview(ban_list_frame, columns=columns, show="headings", height=8, selectmode="browse")
        
        for col in columns:
            self.ban_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.ban_tree, c, False))
            if col == "玩家名称":
                self.ban_tree.column(col, width=160, stretch=True, minwidth=140)
            elif col == "封禁原因":
                self.ban_tree.column(col, width=220, stretch=True, minwidth=180)
            elif col == "剩余时间":
                self.ban_tree.column(col, width=100, stretch=False)
            else:
                self.ban_tree.column(col, width=140, stretch=False)
        
        ban_tree_frame = ttk.Frame(ban_list_frame)
        ban_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.ban_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ban_scrollbar = ttk.Scrollbar(ban_tree_frame, orient=tk.VERTICAL, command=self.ban_tree.yview)
        ban_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ban_tree.configure(yscrollcommand=ban_scrollbar.set)
        
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
    
    def _create_mute_section(self, parent):
        mute_frame = ttk.LabelFrame(parent, text="禁言玩家", padding="12")
        mute_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(12, 12))
        
        mute_form_frame = ttk.Frame(mute_frame)
        mute_form_frame.pack(fill=tk.X, pady=5)
        
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
        
        mute_list_frame = ttk.LabelFrame(parent, text="禁言玩家列表", padding="12")
        mute_list_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 12))
        
        mute_columns = ("玩家名称", "禁言原因", "禁言日期", "解禁日期", "剩余时间")
        self.mute_tree = ttk.Treeview(mute_list_frame, columns=mute_columns, show="headings", height=6, selectmode="browse")
        
        for col in mute_columns:
            self.mute_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.mute_tree, c, False))
            if col == "玩家名称":
                self.mute_tree.column(col, width=160, stretch=True, minwidth=140)
            elif col == "禁言原因":
                self.mute_tree.column(col, width=220, stretch=True, minwidth=180)
            elif col == "剩余时间":
                self.mute_tree.column(col, width=100, stretch=False)
            else:
                self.mute_tree.column(col, width=140, stretch=False)
        
        mute_tree_frame = ttk.Frame(mute_list_frame)
        mute_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.mute_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        mute_scrollbar = ttk.Scrollbar(mute_tree_frame, orient=tk.VERTICAL, command=self.mute_tree.yview)
        mute_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.mute_tree.configure(yscrollcommand=mute_scrollbar.set)
        
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
    
    def _create_op_section(self, parent):
        op_frame = ttk.LabelFrame(parent, text="管理员管理", padding="12")
        op_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
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
        
        op_form_frame = ttk.Frame(op_frame)
        op_form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(op_form_frame, text="玩家名称:", font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.op_player_var = tk.StringVar()
        self.op_player_combo = ttk.Combobox(op_form_frame, textvariable=self.op_player_var, width=30, state="readonly")
        self.op_player_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=2)
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
        
        op_list_frame = ttk.LabelFrame(parent, text="管理员列表", padding="12")
        op_list_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        
        op_columns = ("玩家名称", "权限等级", "添加时间")
        self.op_tree = ttk.Treeview(op_list_frame, columns=op_columns, show="headings", height=6, selectmode="extended")
        
        for col in op_columns:
            self.op_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.op_tree, c, False))
            if col == "玩家名称":
                self.op_tree.column(col, width=200, stretch=True, minwidth=180)
            elif col == "权限等级":
                self.op_tree.column(col, width=100, anchor=tk.CENTER, stretch=False)
            else:
                self.op_tree.column(col, width=140, stretch=False)
        
        op_tree_frame = ttk.Frame(op_list_frame)
        op_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.op_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        op_scrollbar = ttk.Scrollbar(op_tree_frame, orient=tk.VERTICAL, command=self.op_tree.yview)
        op_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.op_tree.configure(yscrollcommand=op_scrollbar.set)
        
        op_log_frame = ttk.LabelFrame(parent, text="操作记录", padding="12")
        op_log_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(12, 0))
        
        self.op_log_text = scrolledtext.ScrolledText(op_log_frame, height=6)
        self.op_log_text.pack(fill=tk.BOTH, expand=True)
        self.op_log_text.insert(tk.END, "管理员操作记录将在这里显示...\n")
        self.op_log_text.config(state=tk.DISABLED)
    
    def create_player_management_tab(self):
        player_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(player_frame, text="玩家管理")
        
        whitelist_frame = ttk.LabelFrame(player_frame, text="白名单管理", padding="10")
        whitelist_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(whitelist_frame, text="玩家名称:").grid(row=0, column=0, sticky=tk.W)
        self.whitelist_player_var = tk.StringVar()
        whitelist_player_entry = ttk.Entry(whitelist_frame, textvariable=self.whitelist_player_var, width=20)
        whitelist_player_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(whitelist_frame, text="添加到白名单", 
                  command=self.whitelist_manager.add_to_whitelist).grid(row=0, column=2, padx=(5, 0))
        ttk.Button(whitelist_frame, text="从白名单移除", 
                  command=self.whitelist_manager.remove_from_whitelist).grid(row=0, column=3, padx=(5, 0))
        ttk.Button(whitelist_frame, text="重载白名单", 
                  command=self.whitelist_manager.reload_whitelist).grid(row=0, column=4, padx=(5, 0))
        
        whitelist_list_frame = ttk.LabelFrame(player_frame, text="白名单列表", padding="10")
        whitelist_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        whitelist_columns = ("玩家名称", "添加日期")
        self.whitelist_tree = ttk.Treeview(whitelist_list_frame, columns=whitelist_columns, show="headings", height=10, selectmode="browse")
        
        for col in whitelist_columns:
            self.whitelist_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.whitelist_tree, c, False))
            if col == "玩家名称":
                self.whitelist_tree.column(col, width=200, stretch=True, minwidth=150)
            else:
                self.whitelist_tree.column(col, width=130, stretch=False)
        
        self.whitelist_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        whitelist_scrollbar = ttk.Scrollbar(whitelist_list_frame, orient=tk.VERTICAL, command=self.whitelist_tree.yview)
        whitelist_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.whitelist_tree.configure(yscrollcommand=whitelist_scrollbar.set)
        
        whitelist_buttons_frame = ttk.Frame(whitelist_list_frame)
        whitelist_buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(whitelist_buttons_frame, text="刷新列表", 
                  command=self.whitelist_manager.load_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="启用白名单", 
                  command=self.whitelist_manager.enable_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="禁用白名单", 
                  command=self.whitelist_manager.disable_whitelist).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(whitelist_buttons_frame, text="导出白名单", 
                  command=self.whitelist_manager.export_whitelist).pack(side=tk.LEFT)
        
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
        
        player_frame.columnconfigure(0, weight=1)
        player_frame.rowconfigure(1, weight=1)
        whitelist_frame.columnconfigure(1, weight=1)
        whitelist_list_frame.columnconfigure(0, weight=1)
        whitelist_list_frame.rowconfigure(0, weight=1)
        player_data_frame.columnconfigure(1, weight=1)
        
        self.whitelist_manager.load_whitelist()
    
    def create_world_management_tab(self):
        world_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(world_frame, text="世界管理")
        
        backup_frame = ttk.LabelFrame(world_frame, text="世界备份", padding="12")
        backup_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        backup_buttons_frame = ttk.Frame(backup_frame)
        backup_buttons_frame.pack(fill=tk.X, pady=5)
        
        create_backup_button = ttk.Button(backup_buttons_frame, text="创建备份", 
                  command=self.world_manager.create_backup, width=14)
        create_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(create_backup_button, "创建世界备份")
        
        restore_backup_button = ttk.Button(backup_buttons_frame, text="恢复备份", 
                  command=self.world_manager.restore_backup, width=14)
        restore_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(restore_backup_button, "从备份恢复世界")
        
        open_backup_button = ttk.Button(backup_buttons_frame, text="打开备份目录", 
                  command=self.world_manager.open_backup_folder, width=16)
        open_backup_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(open_backup_button, "打开备份文件所在目录")
        
        auto_backup_button = ttk.Button(backup_buttons_frame, text="自动备份设置", 
                  command=self.world_manager.auto_backup_settings, width=16)
        auto_backup_button.pack(side=tk.LEFT, pady=3)
        self.add_tooltip(auto_backup_button, "设置自动备份选项")
        
        backup_list_frame = ttk.LabelFrame(backup_frame, text="备份列表", padding="12")
        backup_list_frame.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        
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
            else:
                self.backup_tree.column(col, width=80, anchor="center", stretch=False)
        
        backup_tree_frame = ttk.Frame(backup_list_frame)
        backup_tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        backup_scrollbar = ttk.Scrollbar(backup_tree_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        backup_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.backup_tree.configure(yscrollcommand=backup_scrollbar.set)
        
        backup_actions_frame = ttk.Frame(backup_list_frame)
        backup_actions_frame.pack(fill=tk.X, pady=(0, 5))
        
        refresh_backup_button = ttk.Button(backup_actions_frame, text="刷新列表", 
                  command=self.world_manager.refresh_backup_list, width=12)
        refresh_backup_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(refresh_backup_button, "刷新备份列表")
        
        delete_backup_button = ttk.Button(backup_actions_frame, text="删除备份", 
                  command=self.world_manager.delete_backup, width=12)
        delete_backup_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.add_tooltip(delete_backup_button, "删除选中的备份")
        
        export_backup_button = ttk.Button(backup_actions_frame, text="导出备份", 
                  command=self.world_manager.export_backup, width=12)
        export_backup_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(export_backup_button, "导出备份到指定位置")
        
        import_export_frame = ttk.LabelFrame(world_frame, text="世界导入/导出", padding="12")
        import_export_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        import_export_buttons = ttk.Frame(import_export_frame)
        import_export_buttons.pack(fill=tk.X, pady=5)
        
        import_world_button = ttk.Button(import_export_buttons, text="导入世界", 
                  command=self.world_manager.import_world, width=14)
        import_world_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(import_world_button, "从文件导入世界")
        
        export_world_button = ttk.Button(import_export_buttons, text="导出世界", 
                  command=self.world_manager.export_world, width=14)
        export_world_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(export_world_button, "导出当前世界到文件")
        
        gamerules_frame = ttk.LabelFrame(world_frame, text="游戏规则", padding="12")
        gamerules_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 12))
        
        gamerules_batch_frame = ttk.Frame(gamerules_frame)
        gamerules_batch_frame.pack(fill=tk.X, pady=(0, 8))
        
        apply_all_button = ttk.Button(gamerules_batch_frame, text="应用所有规则", 
                  command=self.world_manager.apply_all_gamerules, width=16)
        apply_all_button.pack(side=tk.LEFT, padx=(0, 10), pady=2)
        self.add_tooltip(apply_all_button, "批量应用所有游戏规则")
        
        reset_button = ttk.Button(gamerules_batch_frame, text="重置为默认", 
                  command=self.world_manager.reset_gamerules, width=12)
        reset_button.pack(side=tk.LEFT, pady=2)
        self.add_tooltip(reset_button, "重置所有游戏规则为默认值")
        
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
        
        self.world_manager.gamerule_vars = {}
        
        gamerules_grid = ttk.Frame(gamerules_frame)
        gamerules_grid.pack(fill=tk.X, pady=5)
        
        for i, (text, rule, default) in enumerate(gamerules):
            rule_frame = ttk.Frame(gamerules_grid)
            rule_frame.pack(fill=tk.X, pady=4)
            
            ttk.Label(rule_frame, text=text, font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 20), pady=2)
            var = tk.StringVar(value=default)
            self.world_manager.gamerule_vars[rule] = var
            
            combo = ttk.Combobox(rule_frame, textvariable=var, 
                        values=["true", "false"], width=12, state="readonly")
            combo.pack(side=tk.LEFT, padx=(0, 20), pady=2)
            
            apply_button = ttk.Button(rule_frame, text="应用", 
                      command=lambda r=rule, v=var: self.world_manager.set_gamerule(r, v.get()), width=10)
            apply_button.pack(side=tk.LEFT, pady=2)
            self.add_tooltip(apply_button, f"应用 {text} 规则")
        
        world_settings_frame = ttk.LabelFrame(world_frame, text="世界设置", padding="12")
        world_settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        settings_buttons_frame = ttk.Frame(world_settings_frame)
        settings_buttons_frame.pack(fill=tk.X, pady=5)
        
        spawn_button = ttk.Button(settings_buttons_frame, text="设置出生点", 
                  command=self.world_manager.set_spawn_point, width=14)
        spawn_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(spawn_button, "设置服务器出生点")
        
        gamemode_button = ttk.Button(settings_buttons_frame, text="更改游戏模式", 
                  command=self.world_manager.change_game_mode, width=14)
        gamemode_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(gamemode_button, "更改服务器游戏模式")
        
        difficulty_button = ttk.Button(settings_buttons_frame, text="更改难度", 
                  command=self.world_manager.change_difficulty, width=14)
        difficulty_button.pack(side=tk.LEFT, padx=(0, 10), pady=3)
        self.add_tooltip(difficulty_button, "更改服务器难度")
        
        time_button = ttk.Button(settings_buttons_frame, text="设置时间", 
                  command=self.world_manager.set_time, width=14)
        time_button.pack(side=tk.LEFT, pady=3)
        self.add_tooltip(time_button, "设置服务器时间")
        
        world_frame.columnconfigure(0, weight=1)
        backup_list_frame.columnconfigure(0, weight=1)
        backup_tree_frame.columnconfigure(0, weight=1)
        backup_tree_frame.rowconfigure(0, weight=1)
        gamerules_grid.columnconfigure(0, weight=1)
    
    def create_plugin_management_tab(self):
        plugin_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(plugin_frame, text="插件管理")
        
        scan_frame = ttk.LabelFrame(plugin_frame, text="插件扫描", padding="10")
        scan_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(scan_frame, text="扫描插件", command=self.scan_plugins).pack(side=tk.LEFT, padx=(0, 10))
        self.plugin_count_var = tk.StringVar(value="插件数量: 0")
        ttk.Label(scan_frame, textvariable=self.plugin_count_var).pack(side=tk.LEFT, padx=(0, 20))
        
        self.plugin_enabled_var = tk.StringVar(value="启用: 0")
        self.plugin_disabled_var = tk.StringVar(value="禁用: 0")
        ttk.Label(scan_frame, textvariable=self.plugin_enabled_var).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(scan_frame, textvariable=self.plugin_disabled_var).pack(side=tk.LEFT)
        
        list_frame = ttk.LabelFrame(plugin_frame, text="插件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("状态", "名称", "版本", "作者", "类型", "最后修改")
        self.plugins_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15, selectmode="browse")
        
        for col in columns:
            self.plugins_tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(self.plugins_tree, c, False))
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
            else:
                self.plugins_tree.column(col, width=160, stretch=False)
        
        self.plugins_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        plugins_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.plugins_tree.yview)
        plugins_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.plugins_tree.configure(yscrollcommand=plugins_scrollbar.set)
        
        detail_frame = ttk.LabelFrame(plugin_frame, text="插件详情", padding="10")
        detail_frame.pack(fill=tk.X, pady=(0, 10))
        
        detail_top_frame = ttk.Frame(detail_frame)
        detail_top_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        
        status_frame = ttk.Frame(detail_top_frame)
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Label(status_frame, text="状态:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.plugin_status_var = tk.StringVar(value="未选择")
        ttk.Label(status_frame, textvariable=self.plugin_status_var, font=('微软雅黑', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(status_frame, text="类型:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.plugin_type_var = tk.StringVar(value="-")
        ttk.Label(status_frame, textvariable=self.plugin_type_var).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        desc_frame = ttk.LabelFrame(detail_frame, text="描述", padding="5")
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        self.plugin_detail_text = scrolledtext.ScrolledText(desc_frame, height=6, width=50)
        self.plugin_detail_text.pack(fill=tk.BOTH, expand=True)
        self.plugin_detail_text.insert(tk.END, "选择插件查看详情...\n")
        self.plugin_detail_text.config(state=tk.DISABLED)
        
        self.plugins_tree.bind("<<TreeviewSelect>>", self.on_plugin_select)
    
    def start_periodic_updates(self):
        self.update_performance_display()
        self.version_detector.detect_version()
        if hasattr(self, 'server_manager') and self.server_manager.server_running:
            self.root.after(5000, self.periodic_player_list_update)
        
        self.start_log_saving()
    
    def start_log_saving(self):
        self.log_manager.save_server_logs()
        self.log_manager.save_performance_logs()
        
        self.log_save_timer = self.root.after(12 * 60 * 60 * 1000, self.log_save_callback)
    
    def log_save_callback(self):
        self.log_manager.save_server_logs()
        self.log_manager.save_performance_logs()
        
        self.log_save_timer = self.root.after(12 * 60 * 60 * 1000, self.log_save_callback)
    
    def periodic_player_list_update(self):
        if hasattr(self, 'server_manager') and self.server_manager.server_running:
            self.update_players_display()
            self.root.after(10000, self.periodic_player_list_update)
    
    def auto_detect_local_ip(self):
        def detect_ip():
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                
                if local_ip.startswith('127.'):
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(("8.8.8.8", 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                    except:
                        pass
                
                self.root.after(0, lambda: self.server_ip_var.set(local_ip))
                self.root.after(0, self.update_server_address_display)
                
            except Exception as e:
                print(f"自动检测IP失败: {e}")
                self.root.after(0, lambda: self.server_ip_var.set("localhost"))
                self.root.after(0, self.update_server_address_display)
        
        threading.Thread(target=detect_ip, daemon=True).start()
    
    def update_server_address_display(self):
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        
        if ip and port:
            address = f"{ip}:{port}"
            self.server_address_var.set(f"服务器地址: {address}")
            
            if ip.startswith('127.'):
                self.server_address_var.set(f"服务器地址: {address} (本地测试地址，其他设备无法连接)")
            elif ip == "localhost":
                self.server_address_var.set(f"服务器地址: {address} (本地测试地址，其他设备无法连接)")
        else:
            self.server_address_var.set("服务器地址: 未配置")
    
    def copy_server_address(self):
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
        def get_public_ip():
            try:
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
        
        threading.Thread(target=update_ip, daemon=True).start()
        messagebox.showinfo("检测中", "正在检测公网IP，请稍候...")
    
    def generate_qr_code(self):
        if not QRCODE_AVAILABLE:
            messagebox.showerror("错误", "需要安装qrcode和PIL库: pip install qrcode[pil]")
            return
        
        ip = self.server_ip_var.get().strip()
        port = self.server_port_var.get().strip()
        
        if not ip or not port:
            messagebox.showwarning("警告", "请先配置服务器地址和端口")
            return
        
        address = f"{ip}:{port}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        qr_window = tk.Toplevel(self.root)
        qr_window.title("服务器连接二维码")
        qr_window.geometry("400x500")
        qr_window.resizable(False, False)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        photo = ImageTk.PhotoImage(qr_image)
        
        qr_label = ttk.Label(qr_window, image=photo)
        qr_label.image = photo
        qr_label.pack(pady=10)
        
        address_label = ttk.Label(qr_window, text=f"服务器地址: {address}", font=("微软雅黑", 12, "bold"))
        address_label.pack(pady=5)
        
        help_text = "使用手机Minecraft扫描此二维码可直接连接服务器"
        help_label = ttk.Label(qr_window, text=help_text, wraplength=350, justify=tk.CENTER)
        help_label.pack(pady=10)
        
        button_frame = ttk.Frame(qr_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="保存二维码", 
                  command=lambda: self.save_qr_code(qr_image)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", 
                  command=qr_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_qr_code(self, qr_image):
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
        result = self.server_manager.start_server()
        if not result:
            messagebox.showerror("错误", "启动服务器失败")
    
    def stop_server(self):
        self.server_manager.stop_server()
    
    def restart_server(self):
        self.server_manager.restart_server()
    
    def quick_command(self, command):
        self.send_server_command(command)
    
    def send_command(self, event=None):
        command = self.command_var.get().strip()
        if not command:
            return
        
        self.send_server_command(command)
        self.command_var.set("")
        self.suggestion_index = -1
    
    def send_server_command(self, command):
        return self.server_manager.send_server_command(command)
    
    def log_message(self, message):
        self.log_manager.log_message(message)
    
    def update_players_display(self):
        self.player_manager.update_players_display()
        self.update_ban_mute_player_combos()
    
    def sort_treeview(self, tree, column, reverse):
        items = [(tree.set(k, column), k) for k in tree.get_children('')]
        
        try:
            items.sort(key=lambda x: float(x[0]), reverse=reverse)
        except ValueError:
            items.sort(key=lambda x: x[0], reverse=reverse)
        
        for index, (val, k) in enumerate(items):
            tree.move(k, '', index)
        
        tree.heading(column, command=lambda c=column: self.sort_treeview(tree, c, not reverse))
    
    def _on_player_filter_complete(self, filtered_players):
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
        if isinstance(minutes, str):
            return minutes
        
        hours = minutes // 60
        mins = minutes % 60
        
        if hours > 0:
            return f"{hours}小时{mins}分钟"
        else:
            return f"{mins}分钟"
    
    def on_player_select(self, event):
        selection = self.players_tree.selection()
        if selection:
            item = selection[0]
            values = self.players_tree.item(item)['values']
            if len(values) >= 6:
                status, player, position, ping, gamemode, online_time = values
                self.selected_player_name_var.set(player)
                self.selected_player_pos_var.set(position)
                self.selected_player_ping_var.set(ping)
                self.selected_player_gamemode_var.set(gamemode)
            else:
                player = values[1]
                self.selected_player_name_var.set(player)
                self.selected_player_pos_var.set("-")
                self.selected_player_ping_var.set("-")
                self.selected_player_gamemode_var.set("-")
    
    def on_tab_changed(self, event):
        pass
    
    def update_player_chat_display(self, player):
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
        selection = self.players_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        player = self.players_tree.item(selection[0])['values'][0]
        message = self.chat_message_var.get().strip()
        
        if not message:
            return
            
        self.send_server_command(f"tell {player} {message}")
        self.message_manager.add_message(player, message, is_server=True)
        
        self.chat_message_var.set("")
    
    def get_selected_player(self):
        return self.player_manager.get_selected_player()
    
    def send_message_to_player(self):
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        message = simpledialog.askstring("发送消息", f"发送给 {player} 的消息:")
        
        if message:
            self.send_server_command(f"tell {player} {message}")
            self.message_manager.add_message(player, message, is_server=True)
    
    def kick_player(self):
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        reason = simpledialog.askstring("踢出玩家", f"踢出 {player} 的原因:", initialvalue="违反服务器规则")
        
        if reason is not None:
            self.player_manager.kick_player(player, reason)
    
    def teleport_player(self):
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        destination = simpledialog.askstring("传送玩家", f"将 {player} 传送到:", initialvalue="~ ~ ~")
        
        if destination:
            self.player_manager.teleport_player(player, destination)
    
    def op_player(self):
        player = self.get_selected_player()
        if not player:
            messagebox.showwarning("警告", "请先选择玩家")
            return
            
        self.player_manager.op_player(player)
    
    def refresh_player_list(self):
        self.player_manager.refresh_player_list()
    
    def update_performance_display(self):
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
            
            self.update_performance_history()
            
        except Exception as e:
            print(f"更新性能显示时出错: {e}")
        
        if hasattr(self, 'auto_refresh_var') and self.auto_refresh_var.get() and hasattr(self, 'server_manager') and self.server_manager.server_running:
            self.performance_update_timer = self.root.after(2000, self.update_performance_display)
    
    def update_performance_history(self):
        if not PSUTIL_AVAILABLE or not hasattr(self, 'performance_history_text'):
            return
            
        history = self.performance_monitor.get_performance_history()
        if not history:
            return
            
        self.performance_history_text.config(state=tk.NORMAL)
        self.performance_history_text.delete(1.0, tk.END)
        
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
    
    def on_command_key_release(self, event):
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
    
    def on_ban_player_selected(self, event=None):
        pass
    
    def on_mute_player_selected(self, event=None):
        pass
    
    def on_ban_combo_focus(self, event=None):
        self.update_ban_combo_values()
    
    def on_mute_combo_focus(self, event=None):
        self.update_mute_combo_values()
    
    def update_ban_combo_values(self):
        players = self.player_manager.players_online if hasattr(self, 'player_manager') else []
        current_text = self.ban_player_var.get().strip()
        if current_text:
            filtered = [p for p in players if current_text.lower() in p.lower()]
            self.ban_player_combo['values'] = filtered if filtered else players
        else:
            self.ban_player_combo['values'] = players
        return None
    
    def update_mute_combo_values(self):
        players = self.player_manager.players_online if hasattr(self, 'player_manager') else []
        current_text = self.mute_player_var.get().strip()
        if current_text:
            filtered = [p for p in players if current_text.lower() in p.lower()]
            self.mute_player_combo['values'] = filtered if filtered else players
        else:
            self.mute_player_combo['values'] = players
        return None
    
    def update_ban_mute_player_combos(self):
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
        if self.ban_type_var.get() == "永久":
            self.ban_time_combo.config(state="disabled")
        else:
            self.ban_time_combo.config(state="readonly")
    
    def ban_player(self):
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
            self.load_banned_players()
            messagebox.showinfo("成功", f"已封禁玩家: {player}")
    
    def update_ban_times(self):
        self.ban_manager.update_ban_times()
    
    def load_banned_players(self):
        for item in self.ban_tree.get_children():
            self.ban_tree.delete(item)
        
        current_time = datetime.now()
        for ban in self.banned_players:
            player = ban["player"]
            reason = ban["reason"]
            ban_date = ban["ban_date"]
            unban_date = ban["unban_date"]
            ban_type = ban.get("ban_type", "永久")
            
            time_left = "永久"
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
                    self.banned_players.remove(ban)
                    if player in self.ban_manager.temp_bans:
                        del self.ban_manager.temp_bans[player]
                    continue
            
            self.ban_tree.insert("", tk.END, values=(player, reason, ban_date, unban_date, time_left))
        
        if hasattr(self, 'op_player_combo'):
            self.update_player_combo()
    
    def pardon_player(self):
        selection = self.ban_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解封的玩家")
            return
        
        player = self.ban_tree.item(selection[0])['values'][0]
        
        result = self.ban_manager.pardon_player(player)
        if result:
            self.load_banned_players()
            messagebox.showinfo("成功", f"已解封玩家: {player}")
    
    def on_mute_type_changed(self, event=None):
        if self.mute_type_var.get() == "永久":
            self.mute_time_combo.config(state="disabled")
        else:
            self.mute_time_combo.config(state="readonly")
    
    def mute_player(self):
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
            self.load_muted_players()
            messagebox.showinfo("成功", f"已禁言玩家: {player}")
    
    def unmute_player(self):
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
        selection = self.mute_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要解禁的玩家")
            return
        
        player = self.mute_tree.item(selection[0])['values'][0]
        
        result = self.ban_manager.unmute_player(player)
        if result:
            self.load_muted_players()
            messagebox.showinfo("成功", f"已解除玩家 {player} 的禁言")
    
    def load_muted_players(self):
        for item in self.mute_tree.get_children():
            self.mute_tree.delete(item)
        
        current_time = datetime.now()
        players_to_remove = []
        
        for player, mute_info in self.ban_manager.muted_players.items():
            reason = mute_info.get("reason", "无")
            mute_date = mute_info.get("mute_date", "未知")
            unmute_date = mute_info.get("unmute_date", "永久")
            mute_type = mute_info.get("type", "permanent")
            
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
                    players_to_remove.append(player)
                    continue
            
            if isinstance(mute_date, datetime):
                mute_date_str = mute_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                mute_date_str = str(mute_date)
                
            if isinstance(unmute_date, datetime):
                unmute_date_str = unmute_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                unmute_date_str = str(unmute_date)
            
            self.mute_tree.insert("", tk.END, values=(player, reason, mute_date_str, unmute_date_str, time_left))
        
        for player in players_to_remove:
            del self.ban_manager.muted_players[player]
        
        if hasattr(self, 'op_player_combo'):
            self.update_player_combo()
    
    def update_mute_times(self):
        self.ban_manager.update_mute_times()
    
    def add_op(self):
        player = self.op_player_var.get().strip()
        level = self.op_level_var.get()
        if not player:
            messagebox.showwarning("警告", "请选择玩家")
            return
        
        for op_name, _ in self.ops:
            if op_name == player:
                messagebox.showinfo("提示", f"玩家 {player} 已经是管理员")
                return
        
        result = messagebox.askyesno("确认", f"确定要将玩家 {player} 设为管理员，权限等级: {level}吗？")
        if result:
            self.send_server_command(f"op {player}")
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.ops.append((player, level, current_time))
            self.load_ops()
            message = f"已将玩家 {player} 设为管理员，权限等级: {level}"
            messagebox.showinfo("成功", message)
            self.log_op_action(message)
    
    def remove_op(self):
        player = self.op_player_var.get().strip()
        if not player:
            selection = self.op_tree.selection()
            if selection:
                player = self.op_tree.item(selection[0])['values'][0]
            else:
                messagebox.showwarning("警告", "请选择玩家或从列表中选择管理员")
                return
            
        result = messagebox.askyesno("确认", f"确定要移除玩家 {player} 的管理员权限吗？")
        if result:
            self.send_server_command(f"deop {player}")
            self.ops = [op for op in self.ops if op[0] != player]
            self.load_ops()
            message = f"已移除玩家 {player} 的管理员权限"
            messagebox.showinfo("成功", message)
            self.log_op_action(message)
    
    def update_player_combo(self):
        player_names = set()
        
        for name, _ in self.ops:
            player_names.add(name)
        
        for name, _ in self.whitelist:
            player_names.add(name)
        
        for ban in self.banned_players:
            player_names.add(ban["player"])
        
        for item in self.players_tree.get_children():
            player_name = self.players_tree.item(item)["values"][1]
            player_names.add(player_name)
        
        sorted_players = sorted(player_names)
        
        self.op_player_combo['values'] = sorted_players
        
        if sorted_players:
            self.op_player_var.set(sorted_players[0])
    
    def load_ops(self):
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)
        
        for op in self.ops:
            if len(op) >= 3:
                name, level, time_added = op
                self.op_tree.insert("", tk.END, values=(name, level, time_added))
            else:
                name, level = op
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.op_tree.insert("", tk.END, values=(name, level, current_time))
        
        self.update_player_combo()
    
    def search_ops(self, event=None):
        search_term = self.op_search_var.get().strip().lower()
        
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)
        
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
        selected_items = self.op_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要移除的管理员")
            return
        
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
                    self.ops = [op for op in self.ops if op[0] != player]
                self.load_ops()
                message = f"已批量移除管理员: {', '.join(selected_players)}"
                messagebox.showinfo("成功", message)
                self.log_op_action(message)
            except Exception as e:
                error_message = f"批量移除管理员时出错: {str(e)}"
                self.log_op_action(error_message)
                messagebox.showerror("错误", error_message)
    
    def batch_update_op_levels(self):
        selected_items = self.op_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择要更新权限等级的管理员")
            return
        
        new_level = simpledialog.askstring("更新权限等级", "请输入新的权限等级 (1-4):", initialvalue="4")
        if not new_level or not new_level.isdigit() or not 1 <= int(new_level) <= 4:
            messagebox.showwarning("警告", "请输入有效的权限等级 (1-4)")
            return
        
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
                    for i, op in enumerate(self.ops):
                        if op[0] == player:
                            if len(op) >= 3:
                                self.ops[i] = (player, new_level, op[2])
                            else:
                                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                self.ops[i] = (player, new_level, current_time)
                self.load_ops()
                message = f"已批量更新管理员权限等级为 {new_level}: {', '.join(selected_players)}"
                messagebox.showinfo("成功", message)
                self.log_op_action(message)
            except Exception as e:
                error_message = f"批量更新权限等级时出错: {str(e)}"
                self.log_op_action(error_message)
                messagebox.showerror("错误", error_message)
    
    def log_op_action(self, message):
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
    
    def view_player_data(self):
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        player_data_dir = os.path.join(self.server_dir_var.get(), "world", "playerdata")
        if os.path.exists(player_data_dir):
            player_files = [f for f in os.listdir(player_data_dir) if f.endswith('.dat')]
            
            if player_files:
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
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        result = messagebox.askyesno("确认", f"确定要重置玩家 {player} 的数据吗？此操作不可撤销！")
        if result:
            self.send_server_command(f"kick {player} 你的数据已被重置")
            messagebox.showinfo("成功", f"玩家 {player} 的数据已重置")
    
    def teleport_to_player(self):
        player = self.player_data_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        target = simpledialog.askstring("传送玩家", f"将谁传送到 {player}:", parent=self.root)
        if target:
            self.send_server_command(f"tp {target} {player}")
    
    def scan_plugins(self):
        self.plugin_manager.server_dir = self.server_dir_var.get()
        self.plugin_manager.plugins_dir = os.path.join(self.server_dir_var.get(), "plugins")
        
        plugins = self.plugin_manager.scan_plugins()
        
        for item in self.plugins_tree.get_children():
            self.plugins_tree.delete(item)
        
        enabled_count = 0
        disabled_count = 0
        
        for plugin in plugins:
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
        
        self.plugin_count_var.set(f"插件数量: {len(plugins)}")
        self.plugin_enabled_var.set(f"启用: {enabled_count}")
        self.plugin_disabled_var.set(f"禁用: {disabled_count}")
        
        self.plugin_detail_text.config(state=tk.NORMAL)
        self.plugin_detail_text.delete(1.0, tk.END)
        self.plugin_detail_text.insert(tk.END, "选择插件查看详情...\n")
        self.plugin_detail_text.config(state=tk.DISABLED)
        
        self.plugin_name_var.set("-")
        self.plugin_version_var.set("-")
        self.plugin_author_var.set("-")
        self.plugin_status_var.set("未选择")
        self.plugin_type_var.set("-")
    
    def on_plugin_select(self, event):
        selected_items = self.plugins_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        plugin_name = self.plugins_tree.item(item, 'tags')[0]
        
        plugin = self.plugin_manager.get_plugin_by_name(plugin_name)
        if plugin:
            self.plugin_name_var.set(plugin['name'])
            self.plugin_version_var.set(plugin['version'])
            self.plugin_author_var.set(plugin['author'])
            self.plugin_type_var.set(plugin['type'])
            
            status = "启用" if plugin.get('enabled', True) else "禁用"
            self.plugin_status_var.set(status)
            
            self.plugin_detail_text.config(state=tk.NORMAL)
            self.plugin_detail_text.delete(1.0, tk.END)
            if 'description' in plugin and plugin['description']:
                self.plugin_detail_text.insert(tk.END, plugin['description'])
            else:
                self.plugin_detail_text.insert(tk.END, "该插件没有描述信息")
            self.plugin_detail_text.config(state=tk.DISABLED)
    
    def save_config(self):
        self.config_manager.save_config()
    
    def load_config(self):
        self.config_manager.load_config()
    
    def clear_logs(self):
        self.log_manager.clear_logs()
    
    def export_logs(self):
        self.log_manager.export_logs()
    
    def search_logs(self):
        self.log_manager.search_logs()
    
    def load_server_data(self):
        self.server_properties_manager.load_server_properties()
        self.load_banned_players()
        self.load_ops()
        self.whitelist_manager.load_whitelist()
    
    def load_server_properties(self):
        self.server_properties_manager.load_server_properties()
    
    def set_property(self, prop, value):
        self.server_properties_manager.set_property(prop, value)
    
    def validate_property(self, prop, var, validator):
        self.server_properties_manager.validate_property(prop, var, validator)
    
    def set_property_with_validation(self, prop, value):
        self.server_properties_manager.set_property_with_validation(prop, value)
    
    def apply_all_properties_with_validation(self):
        self.server_properties_manager.apply_all_properties_with_validation()
    
    def validate_port(self, value):
        return self.server_properties_manager.validate_port(value)
    
    def validate_max_players(self, value):
        return self.server_properties_manager.validate_max_players(value)
    
    def validate_view_distance(self, value):
        return self.server_properties_manager.validate_view_distance(value)
    
    def validate_max_players_setting(self, event=None):
        return self.server_properties_manager.validate_max_players_setting(event)
    
    def apply_max_players_setting(self):
        self.server_properties_manager.apply_max_players_setting()
    
    def browse_jar_path(self):
        filename = filedialog.askopenfilename(
            title="选择服务器JAR文件",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_path_var.set(filename)
    
    def browse_server_dir(self):
        directory = filedialog.askdirectory(title="选择服务器目录")
        if directory:
            self.server_dir_var.set(directory)
            self.load_server_data()
    
    def browse_java_path(self):
        filename = filedialog.askopenfilename(
            title="选择Java可执行文件",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.java_path_var.set(filename)


if __name__ == "__main__":
    root = tk.Tk()
    app = MCServerControlPanel(root)
    root.mainloop()
