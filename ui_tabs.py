import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import os
import threading
import time
from datetime import datetime
import shutil
import zipfile
import tempfile
import webbrowser
from tkinter import filedialog

try:
    import platform
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import qrcode
    from PIL import Image, ImageTk
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class ResponsiveMixin:
    """响应式布局混入类"""
    
    def get_responsive_columns(self, breakpoint):
        """根据屏幕断点获取列数"""
        columns_map = {
            'xs': 2,
            'sm': 2,
            'md': 3,
            'lg': 4,
            'xl': 4
        }
        return columns_map.get(breakpoint, 4)
    
    def get_responsive_padding(self, breakpoint):
        """根据屏幕断点获取内边距"""
        padding_map = {
            'xs': 5,
            'sm': 8,
            'md': 10,
            'lg': 12,
            'xl': 15
        }
        return padding_map.get(breakpoint, 10)
    
    def get_responsive_font_size(self, breakpoint):
        """根据屏幕断点获取字体大小"""
        font_map = {
            'xs': 8,
            'sm': 9,
            'md': 10,
            'lg': 11,
            'xl': 12
        }
        return font_map.get(breakpoint, 10)


class DashboardTab(ResponsiveMixin):
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
        self.quick_cmd_buttons = []
    
    def create(self):
        dashboard_frame = ttk.Frame(self.parent, padding="10")
        
        self._create_status_section(dashboard_frame)
        self._create_quick_commands(dashboard_frame)
        self._create_main_content(dashboard_frame)
        self._create_chat_section(dashboard_frame)
        self._create_command_section(dashboard_frame)
        
        # 注册响应式回调
        if hasattr(self.panel, 'responsive_manager'):
            self.panel.responsive_manager.add_resize_callback(self._on_resize)
        
        return dashboard_frame
    
    def _on_resize(self, width, height, breakpoint):
        """响应窗口大小变化"""
        self._update_quick_commands_layout(breakpoint)
        self._update_treeview_columns(breakpoint)
    
    def _update_quick_commands_layout(self, breakpoint):
        """更新快速命令按钮布局"""
        if not self.quick_cmd_buttons:
            return
        
        columns = self.get_responsive_columns(breakpoint)
        for idx, btn in enumerate(self.quick_cmd_buttons):
            row = idx // columns
            col = idx % columns
            btn.grid(row=row, column=col, padx=6, pady=6, sticky=tk.W+tk.E)
    
    def _update_treeview_columns(self, breakpoint):
        """更新玩家列表列宽"""
        if not hasattr(self.panel, 'players_tree'):
            return
        
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
                self.panel.players_tree.column(col, width=width)
    
    def _create_status_section(self, parent):
        status_frame = ttk.LabelFrame(parent, text="服务器状态", padding="12")
        status_frame.pack(fill=tk.X, pady=(0, 12))
        
        status_content_frame = ttk.Frame(status_frame)
        status_content_frame.pack(fill=tk.X)
        
        status_info_frame = ttk.Frame(status_content_frame)
        status_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.panel.status_var = tk.StringVar(value="服务器状态: 已停止")
        status_label = ttk.Label(status_info_frame, textvariable=self.panel.status_var, font=("微软雅黑", 12, "bold"))
        status_label.pack(anchor=tk.W, pady=(0, 8))
        
        info_grid = ttk.Frame(status_info_frame)
        info_grid.pack(fill=tk.X, pady=(0, 5))
        
        self.panel.server_address_var = tk.StringVar(value="服务器地址: 未配置")
        server_address_label = ttk.Label(info_grid, textvariable=self.panel.server_address_var, font=("微软雅黑", 10))
        server_address_label.pack(anchor=tk.W, pady=(0, 3))
        
        info_row = ttk.Frame(info_grid)
        info_row.pack(fill=tk.X, pady=(0, 3))
        
        self.panel.players_var = tk.StringVar(value="在线玩家: 0/20")
        players_label = ttk.Label(info_row, textvariable=self.panel.players_var, font=("微软雅黑", 10))
        players_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.panel.performance_var = tk.StringVar(value="内存使用: N/A | CPU使用: N/A")
        performance_label = ttk.Label(info_row, textvariable=self.panel.performance_var, font=("微软雅黑", 10))
        performance_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.panel.version_var = tk.StringVar(value="服务器版本: 未检测")
        version_label = ttk.Label(info_row, textvariable=self.panel.version_var, font=("微软雅黑", 10))
        version_label.pack(side=tk.LEFT)
        
        button_frame = ttk.Frame(status_content_frame)
        button_frame.pack(side=tk.RIGHT, pady=5)
        
        self.panel.start_button = ttk.Button(button_frame, text="启动服务器", command=self.panel.start_server, width=12)
        self.panel.start_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.panel.add_tooltip(self.panel.start_button, "启动Minecraft服务器")
        
        self.panel.stop_button = ttk.Button(button_frame, text="停止服务器", command=self.panel.stop_server, state=tk.DISABLED, width=12)
        self.panel.stop_button.pack(side=tk.LEFT, padx=(0, 8), pady=2)
        self.panel.add_tooltip(self.panel.stop_button, "安全停止Minecraft服务器")
        
        self.panel.restart_button = ttk.Button(button_frame, text="重启服务器", command=self.panel.restart_server, state=tk.DISABLED, width=12)
        self.panel.restart_button.pack(side=tk.LEFT, pady=2)
        self.panel.add_tooltip(self.panel.restart_button, "重启Minecraft服务器")
        
        address_config_frame = ttk.Frame(status_frame)
        address_config_frame.pack(fill=tk.X, pady=(12, 0))
        
        address_config_inner = ttk.Frame(address_config_frame)
        address_config_inner.pack(fill=tk.X)
        
        ttk.Label(address_config_inner, text="服务器IP:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        server_ip_entry = ttk.Entry(address_config_inner, textvariable=self.panel.server_ip_var, width=18)
        server_ip_entry.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        
        ttk.Label(address_config_inner, text="端口:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        server_port_entry = ttk.Entry(address_config_inner, textvariable=self.panel.server_port_var, width=10)
        server_port_entry.pack(side=tk.LEFT, padx=(0, 12), pady=2)
        
        button_group = ttk.Frame(address_config_inner)
        button_group.pack(side=tk.RIGHT)
        
        detect_public_ip_btn = ttk.Button(button_group, text="检测公网IP", 
                  command=self.panel.detect_public_ip, width=10)
        detect_public_ip_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.panel.add_tooltip(detect_public_ip_btn, "检测当前网络的公网IP地址")
        
        detect_local_ip_btn = ttk.Button(button_group, text="检测本地IP", 
                  command=self.panel.auto_detect_local_ip, width=10)
        detect_local_ip_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.panel.add_tooltip(detect_local_ip_btn, "检测本地网络IP地址")
        
        copy_address_btn = ttk.Button(button_group, text="复制地址", 
                  command=self.panel.copy_server_address, width=10)
        copy_address_btn.pack(side=tk.LEFT, padx=(0, 6), pady=2)
        self.panel.add_tooltip(copy_address_btn, "复制服务器地址到剪贴板")
        
        if QRCODE_AVAILABLE:
            qr_code_btn = ttk.Button(button_group, text="生成二维码", 
                      command=self.panel.generate_qr_code, width=10)
            qr_code_btn.pack(side=tk.LEFT, pady=2)
            self.panel.add_tooltip(qr_code_btn, "生成服务器连接二维码")
    
    def _create_quick_commands(self, parent):
        quick_cmd_frame = ttk.LabelFrame(parent, text="快速命令", padding="12")
        quick_cmd_frame.pack(fill=tk.X, pady=(0, 12))
        
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
        self.cmd_buttons_frame = cmd_buttons_frame
        
        # 清空之前的按钮列表
        self.quick_cmd_buttons = []
        
        for i, (text, cmd) in enumerate(cmd_buttons):
            btn = ttk.Button(cmd_buttons_frame, text=text, 
                            command=lambda c=cmd: self.panel.quick_command(c),
                            style="TButton")
            btn.grid(row=i//4, column=i%4, padx=6, pady=6, sticky=tk.W+tk.E)
            self.quick_cmd_buttons.append(btn)
            tooltip_text = f"执行命令: {cmd}"
            self.panel.add_tooltip(btn, tooltip_text)
        
        # 配置列权重
        for i in range(4):
            cmd_buttons_frame.columnconfigure(i, weight=1)
    
    def _create_main_content(self, parent):
        main_content_frame = ttk.Frame(parent)
        main_content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        
        info_frame = ttk.LabelFrame(main_content_frame, text="服务器信息", padding="12")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        
        self.panel.info_text = scrolledtext.ScrolledText(info_frame, height=12)
        self.panel.info_text.pack(fill=tk.BOTH, expand=True)
        self.panel.info_text.insert(tk.END, "服务器信息将在这里显示...\n")
        self.panel.info_text.config(state=tk.DISABLED)
        
        players_frame = ttk.LabelFrame(main_content_frame, text="在线玩家", padding="12")
        players_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))
        
        self.panel.player_filter_ui = self.panel.PlayerFilterUI(
            players_frame, 
            self.panel, 
            self.panel.player_filter,
            on_filter_callback=self.panel._on_player_filter_complete
        )
        self.panel.player_filter_ui.get_filter_frame().pack(fill=tk.X, pady=(0, 8))
        
        player_stats_frame = ttk.Frame(players_frame)
        player_stats_frame.pack(fill=tk.X, pady=(0, 12))
        
        self.panel.players_var = tk.StringVar(value="在线玩家: 0/20")
        ttk.Label(player_stats_frame, textvariable=self.panel.players_var, font=('微软雅黑', 10, 'bold')).pack(side=tk.LEFT)
        
        self.panel.player_activity_var = tk.StringVar(value="活跃度: 低")
        ttk.Label(player_stats_frame, textvariable=self.panel.player_activity_var).pack(side=tk.RIGHT)
        
        columns = ("状态", "玩家名称", "位置", "延迟", "游戏模式", "在线时间")
        self.panel.players_tree = ttk.Treeview(players_frame, columns=columns, show="headings", height=12, selectmode="browse")
        
        for col in columns:
            self.panel.players_tree.heading(col, text=col, command=lambda c=col: self.panel.sort_treeview(self.panel.players_tree, c, False))
            if col == "状态":
                self.panel.players_tree.column(col, width=65, anchor=tk.CENTER, stretch=False)
            elif col == "玩家名称":
                self.panel.players_tree.column(col, width=150, stretch=True, minwidth=130)
            elif col == "位置":
                self.panel.players_tree.column(col, width=190, stretch=True, minwidth=160)
            elif col == "延迟":
                self.panel.players_tree.column(col, width=75, anchor=tk.CENTER, stretch=False)
            elif col == "游戏模式":
                self.panel.players_tree.column(col, width=95, stretch=False)
            else:
                self.panel.players_tree.column(col, width=115, stretch=False)
        
        players_tree_frame = ttk.Frame(players_frame)
        players_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.panel.players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        players_scrollbar = ttk.Scrollbar(players_tree_frame, orient=tk.VERTICAL, command=self.panel.players_tree.yview)
        players_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.panel.players_tree.configure(yscrollcommand=players_scrollbar.set)
        
        player_detail_frame = ttk.LabelFrame(players_frame, text="玩家详情", padding="8")
        player_detail_frame.pack(fill=tk.X, pady=(12, 0))
        
        detail_grid = ttk.Frame(player_detail_frame)
        detail_grid.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(detail_grid, text="名称:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        self.panel.selected_player_name_var = tk.StringVar(value="未选择")
        ttk.Label(detail_grid, textvariable=self.panel.selected_player_name_var).grid(row=0, column=1, sticky=tk.W, pady=3, padx=(0, 30))
        
        ttk.Label(detail_grid, text="位置:", font=('微软雅黑', 10, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=3, padx=(0, 10))
        self.panel.selected_player_pos_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.panel.selected_player_pos_var).grid(row=0, column=3, sticky=tk.W, pady=3)
        
        ttk.Label(detail_grid, text="延迟:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3, padx=(0, 10))
        self.panel.selected_player_ping_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.panel.selected_player_ping_var).grid(row=1, column=1, sticky=tk.W, pady=3, padx=(0, 30))
        
        ttk.Label(detail_grid, text="游戏模式:", font=('微软雅黑', 10, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=3, padx=(0, 10))
        self.panel.selected_player_gamemode_var = tk.StringVar(value="-")
        ttk.Label(detail_grid, textvariable=self.panel.selected_player_gamemode_var).grid(row=1, column=3, sticky=tk.W, pady=3)
        
        detail_grid.columnconfigure(1, weight=1)
        detail_grid.columnconfigure(3, weight=1)
        
        player_buttons_frame = ttk.Frame(players_frame)
        player_buttons_frame.pack(fill=tk.X, pady=(8, 0))
        
        buttons = [
            ("发送消息", self.panel.send_message_to_player, "向选中的玩家发送消息"),
            ("踢出玩家", self.panel.kick_player, "将选中的玩家踢出服务器"),
            ("传送玩家", self.panel.teleport_player, "将选中的玩家传送到指定位置"),
            ("设为管理员", self.panel.op_player, "将选中的玩家设为服务器管理员"),
            ("刷新列表", self.panel.refresh_player_list, "刷新在线玩家列表")
        ]
        
        for i, (text, cmd, tooltip) in enumerate(buttons):
            btn = ttk.Button(player_buttons_frame, text=text, command=cmd, width=12)
            btn.pack(side=tk.LEFT, padx=4, pady=3)
            self.panel.add_tooltip(btn, tooltip)
        
        self.panel.players_tree.bind('<<TreeviewSelect>>', self.panel.on_player_select)
    
    def _create_chat_section(self, parent):
        chat_frame = ttk.LabelFrame(parent, text="玩家聊天", padding="12")
        chat_frame.pack(fill=tk.X, pady=(12, 0))
        
        self.panel.chat_text = scrolledtext.ScrolledText(chat_frame, height=10)
        self.panel.chat_text.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.panel.chat_text.insert(tk.END, "选择玩家查看聊天记录...\n")
        self.panel.chat_text.config(state=tk.DISABLED)
        
        chat_input_frame = ttk.Frame(chat_frame)
        chat_input_frame.pack(fill=tk.X)
        
        ttk.Label(chat_input_frame, text="发送消息:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        
        self.panel.chat_message_var = tk.StringVar()
        self.panel.chat_entry = ttk.Entry(chat_input_frame, textvariable=self.panel.chat_message_var)
        self.panel.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
        self.panel.chat_entry.bind('<Return>', self.panel.send_chat_message)
        
        self.panel.chat_send_button = ttk.Button(chat_input_frame, text="发送", command=self.panel.send_chat_message, width=8)
        self.panel.chat_send_button.pack(side=tk.LEFT, pady=2)
    
    def _create_command_section(self, parent):
        command_frame = ttk.Frame(parent)
        command_frame.pack(fill=tk.X, pady=(12, 0))
        
        command_input_frame = ttk.Frame(command_frame)
        command_input_frame.pack(fill=tk.X)
        
        ttk.Label(command_input_frame, text="服务器命令:").pack(side=tk.LEFT, padx=(0, 8), pady=2)
        
        self.panel.command_var = tk.StringVar()
        self.panel.command_entry = ttk.Entry(command_input_frame, textvariable=self.panel.command_var)
        self.panel.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)
        self.panel.command_entry.bind('<Return>', self.panel.send_command)
        self.panel.command_entry.bind('<Tab>', self.panel.auto_complete)
        self.panel.command_entry.bind('<KeyRelease>', self.panel.on_command_key_release)
        
        send_button = ttk.Button(command_input_frame, text="发送", command=self.panel.send_command, width=8)
        send_button.pack(side=tk.LEFT, pady=2)
        self.panel.add_tooltip(send_button, "发送命令到服务器")
        
        self.panel.command_hint_var = tk.StringVar(value="输入 /help 查看可用命令")
        command_hint_label = ttk.Label(command_frame, textvariable=self.panel.command_hint_var, foreground="gray")
        command_hint_label.pack(anchor=tk.W, pady=(4, 0))


class PerformanceTab(ResponsiveMixin):
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
    
    def create(self):
        if not PSUTIL_AVAILABLE:
            return None
            
        performance_frame = ttk.Frame(self.parent, padding="10")
        
        self._create_system_info(performance_frame)
        self._create_metrics(performance_frame)
        self._create_server_metrics(performance_frame)
        self._create_chart(performance_frame)
        self._create_controls(performance_frame)
        
        # 注册响应式回调
        if hasattr(self.panel, 'responsive_manager'):
            self.panel.responsive_manager.add_resize_callback(self._on_resize)
        
        return performance_frame
    
    def _on_resize(self, width, height, breakpoint):
        """响应窗口大小变化"""
        # 更新性能图表高度
        if hasattr(self.panel, 'performance_history_text'):
            heights = {'xs': 6, 'sm': 8, 'md': 10, 'lg': 12, 'xl': 15}
            new_height = heights.get(breakpoint, 10)
            self.panel.performance_history_text.config(height=new_height)
    
    def _create_system_info(self, parent):
        system_info_frame = ttk.LabelFrame(parent, text="系统信息", padding="10")
        system_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        if PLATFORM_AVAILABLE:
            os_info = f"操作系统: {platform.system()} {platform.release()}"
            ttk.Label(system_info_frame, text=os_info).grid(row=0, column=0, sticky=tk.W)
            
            try:
                cpu_info = f"CPU: {platform.processor()}"
                ttk.Label(system_info_frame, text=cpu_info).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
            except:
                pass
    
    def _create_metrics(self, parent):
        metrics_frame = ttk.LabelFrame(parent, text="实时性能指标", padding="10")
        metrics_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(metrics_frame, text="CPU使用率:").grid(row=0, column=0, sticky=tk.W)
        self.panel.cpu_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.panel.cpu_var, font=("微软雅黑", 12, "bold")).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(metrics_frame, text="内存使用率:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.panel.memory_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.panel.memory_var, font=("微软雅黑", 12, "bold")).grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(metrics_frame, text="磁盘使用率:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.panel.disk_var = tk.StringVar(value="0%")
        ttk.Label(metrics_frame, textvariable=self.panel.disk_var, font=("微软雅黑", 12, "bold")).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        
        ttk.Label(metrics_frame, text="网络上传:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.panel.network_sent_var = tk.StringVar(value="0 MB")
        ttk.Label(metrics_frame, textvariable=self.panel.network_sent_var).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(metrics_frame, text="网络下载:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        self.panel.network_recv_var = tk.StringVar(value="0 MB")
        ttk.Label(metrics_frame, textvariable=self.panel.network_recv_var).grid(row=1, column=3, sticky=tk.W, pady=(5, 0))
        
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(3, weight=1)
    
    def _create_server_metrics(self, parent):
        server_metrics_frame = ttk.LabelFrame(parent, text="服务器进程资源使用", padding="10")
        server_metrics_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(server_metrics_frame, text="服务器CPU:").grid(row=0, column=0, sticky=tk.W)
        self.panel.server_cpu_var = tk.StringVar(value="0%")
        ttk.Label(server_metrics_frame, textvariable=self.panel.server_cpu_var).grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(server_metrics_frame, text="服务器内存:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        self.panel.server_memory_var = tk.StringVar(value="0 MB")
        ttk.Label(server_metrics_frame, textvariable=self.panel.server_memory_var).grid(row=0, column=3, sticky=tk.W)
    
    def _create_chart(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="性能图表", padding="10")
        chart_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.panel.performance_history_text = scrolledtext.ScrolledText(chart_frame, height=10)
        self.panel.performance_history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.panel.performance_history_text.insert(tk.END, "性能历史数据将在这里显示...\n")
        self.panel.performance_history_text.config(state=tk.DISABLED)
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(3, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        chart_frame.rowconfigure(0, weight=1)
    
    def _create_controls(self, parent):
        controls_frame = ttk.Frame(parent)
        controls_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(controls_frame, text="刷新性能数据", 
                  command=self.panel.update_performance_display).pack(side=tk.LEFT, padx=(0, 5))
        
        self.panel.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, text="自动刷新 (每2秒)", 
                       variable=self.panel.auto_refresh_var).pack(side=tk.LEFT)


class LogsTab(ResponsiveMixin):
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
    
    def create(self):
        logs_frame = ttk.Frame(self.parent, padding="10")
        
        self.panel.log_text = scrolledtext.ScrolledText(logs_frame, height=30, width=100)
        self.panel.log_text.pack(fill=tk.BOTH, expand=True)
        
        log_controls = ttk.Frame(logs_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(log_controls, text="清空日志", 
                  command=self.panel.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="导出日志", 
                  command=self.panel.export_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="查找", 
                  command=self.panel.search_logs).pack(side=tk.LEFT)
        
        # 注册响应式回调
        if hasattr(self.panel, 'responsive_manager'):
            self.panel.responsive_manager.add_resize_callback(self._on_resize)
        
        return logs_frame
    
    def _on_resize(self, width, height, breakpoint):
        """响应窗口大小变化"""
        if hasattr(self.panel, 'log_text'):
            heights = {'xs': 15, 'sm': 20, 'md': 25, 'lg': 30, 'xl': 35}
            new_height = heights.get(breakpoint, 30)
            self.panel.log_text.config(height=new_height)


class SettingsTab(ResponsiveMixin):
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
    
    def create(self):
        settings_frame = ttk.Frame(self.parent, padding="10")
        
        self._create_path_settings(settings_frame)
        self._create_java_settings(settings_frame)
        self._create_other_settings(settings_frame)
        self._create_server_config(settings_frame)
        
        ttk.Button(settings_frame, text="保存设置",
                  command=self.panel.save_config).grid(row=4, column=0, pady=(10, 0))

        settings_frame.columnconfigure(0, weight=1)

        # 注册响应式回调
        if hasattr(self.panel, 'responsive_manager'):
            self.panel.responsive_manager.add_resize_callback(self._on_resize)

        return settings_frame

    def _on_resize(self, width, height, breakpoint):
        """响应窗口大小变化"""
        # 调整输入框宽度
        entry_widths = {'xs': 30, 'sm': 40, 'md': 50, 'lg': 55, 'xl': 60}
        new_width = entry_widths.get(breakpoint, 50)

        # 这里可以添加对设置页面输入框宽度的动态调整
        pass
    
    def _create_path_settings(self, parent):
        path_frame = ttk.LabelFrame(parent, text="服务器路径设置", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(path_frame, text="服务器JAR路径:").grid(row=0, column=0, sticky=tk.W)
        self.panel.jar_path_var = tk.StringVar(value="server.jar")
        jar_path_entry = ttk.Entry(path_frame, textvariable=self.panel.jar_path_var, width=50)
        jar_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(path_frame, text="浏览", 
                  command=self.panel.browse_jar_path).grid(row=0, column=2)
        
        ttk.Label(path_frame, text="服务器目录:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.panel.server_dir_var = tk.StringVar(value=os.getcwd())
        server_dir_entry = ttk.Entry(path_frame, textvariable=self.panel.server_dir_var, width=50)
        server_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(5, 0))
        
        ttk.Button(path_frame, text="浏览", 
                  command=self.panel.browse_server_dir).grid(row=1, column=2, pady=(5, 0))
        
        path_frame.columnconfigure(1, weight=1)
    
    def _create_java_settings(self, parent):
        java_frame = ttk.LabelFrame(parent, text="Java设置", padding="10")
        java_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(java_frame, text="Java路径:").grid(row=0, column=0, sticky=tk.W)
        self.panel.java_path_var = tk.StringVar(value="java")
        java_path_entry = ttk.Entry(java_frame, textvariable=self.panel.java_path_var, width=50)
        java_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(java_frame, text="浏览", 
                  command=self.panel.browse_java_path).grid(row=0, column=2)
        
        ttk.Label(java_frame, text="最小内存:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.panel.min_mem_var = tk.StringVar(value="1G")
        min_mem_entry = ttk.Entry(java_frame, textvariable=self.panel.min_mem_var, width=10)
        min_mem_entry.grid(row=1, column=1, sticky=tk.W, padx=(5, 5), pady=(5, 0))
        
        ttk.Label(java_frame, text="最大内存:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.panel.max_mem_var = tk.StringVar(value="2G")
        max_mem_entry = ttk.Entry(java_frame, textvariable=self.panel.max_mem_var, width=10)
        max_mem_entry.grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        java_frame.columnconfigure(1, weight=1)
    
    def _create_other_settings(self, parent):
        other_frame = ttk.LabelFrame(parent, text="其他设置", padding="10")
        other_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        self.panel.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="启动时自动启动服务器", 
                       variable=self.panel.auto_start_var).grid(row=0, column=0, sticky=tk.W)
        
        self.panel.auto_backup_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="定期自动备份世界", 
                       variable=self.panel.auto_backup_var).grid(row=1, column=0, sticky=tk.W)
        
        self.panel.auto_update_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(other_frame, text="自动检查服务器更新", 
                       variable=self.panel.auto_update_var).grid(row=2, column=0, sticky=tk.W)
    
    def _create_server_config(self, parent):
        server_config_frame = ttk.LabelFrame(parent, text="服务器配置", padding="10")
        server_config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(server_config_frame, text="在线最大玩家数量:").grid(row=0, column=0, sticky=tk.W)
        max_players_entry = ttk.Entry(server_config_frame, textvariable=self.panel.max_players_var, width=15)
        max_players_entry.grid(row=0, column=1, padx=(5, 10), sticky=tk.W)
        max_players_entry.bind('<FocusOut>', self.panel.validate_max_players_setting)
        max_players_entry.bind('<Return>', self.panel.validate_max_players_setting)
        
        ttk.Label(server_config_frame, text="(范围: 1-1000)", foreground="gray").grid(row=0, column=2, sticky=tk.W)
        
        ttk.Label(server_config_frame, textvariable=self.panel.max_players_validation_var, 
                 foreground="red").grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        ttk.Button(server_config_frame, text="应用最大玩家数", 
                  command=self.panel.apply_max_players_setting).grid(row=2, column=0, columnspan=3, pady=(5, 0), sticky=tk.W)


class ServerConfigTab:
    def __init__(self, parent, panel):
        self.parent = parent
        self.panel = panel
    
    def create(self):
        config_frame = ttk.Frame(self.parent, padding="10")
        
        properties_frame = ttk.LabelFrame(config_frame, text="服务器属性", padding="10")
        properties_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.panel.validation_vars = {}
        
        properties = [
            ("服务器端口", "server-port", "25565", self.panel.validate_port),
            ("在线模式", "online-mode", "true", None),
            ("最大玩家数", "max-players", "20", self.panel.validate_max_players),
            ("视图距离", "view-distance", "10", self.panel.validate_view_distance),
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
        
        self.panel.property_vars = {}
        
        for i, (text, prop, default, validator) in enumerate(properties):
            ttk.Label(properties_frame, text=text).grid(row=i, column=0, sticky=tk.W, pady=2)
            
            var = tk.StringVar(value=default)
            self.panel.property_vars[prop] = var
            
            validation_var = tk.StringVar(value="")
            self.panel.validation_vars[prop] = validation_var
            
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
                if validator:
                    var.trace_add("write", lambda *args, p=prop, v=var, val=validator: self.panel.validate_property(p, v, val))
            
            ttk.Label(properties_frame, textvariable=validation_var, foreground="red").grid(row=i, column=2, sticky=tk.W, pady=2)
            
            ttk.Button(properties_frame, text="应用", 
                      command=lambda p=prop, v=var: self.panel.set_property_with_validation(p, v.get())).grid(row=i, column=3, padx=(0, 10), pady=2)
        
        ttk.Button(properties_frame, text="应用所有更改", 
                  command=self.panel.apply_all_properties_with_validation).grid(row=len(properties), column=0, columnspan=4, pady=(10, 0))
        
        config_frame.columnconfigure(0, weight=1)
        properties_frame.columnconfigure(1, weight=1)
        
        return config_frame
