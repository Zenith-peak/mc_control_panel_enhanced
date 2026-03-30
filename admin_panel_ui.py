"""
管理员面板UI模块 - 重构版
提供现代化的卡片式布局、响应式设计和增强的交互体验
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime, timedelta
import threading
import time


class CardFrame:
    """卡片容器类 - 提供现代化的卡片式UI组件"""
    
    def __init__(self, parent, title=None, padding="15", bg_color="#ffffff", 
                 border_color="#e2e8f0", hover_color="#3b82f6", shadow=True):
        self.parent = parent
        self.title = title
        self.bg_color = bg_color
        self.border_color = border_color
        self.hover_color = hover_color
        self.shadow = shadow
        
        # 创建主容器
        self.main_frame = tk.Frame(parent, bg=bg_color, padx=1, pady=1)
        
        # 创建内容框架
        self.content_frame = tk.Frame(self.main_frame, bg=bg_color, padx=padding, pady=padding)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 如果有标题，添加标题栏
        if title:
            self.title_frame = tk.Frame(self.content_frame, bg=bg_color)
            self.title_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.title_label = tk.Label(
                self.title_frame, 
                text=title,
                font=('微软雅黑', 11, 'bold'),
                bg=bg_color,
                fg="#1e293b"
            )
            self.title_label.pack(anchor=tk.W)
            
            # 添加分隔线
            self.separator = tk.Frame(self.content_frame, height=2, bg="#e2e8f0")
            self.separator.pack(fill=tk.X, pady=(0, 10))
        
        # 绑定悬停效果
        self._bind_hover_effects()
    
    def _bind_hover_effects(self):
        """绑定悬停效果"""
        def on_enter(event):
            self.main_frame.config(bg=self.hover_color)
            if hasattr(self, 'separator'):
                self.separator.config(bg=self.hover_color)
        
        def on_leave(event):
            self.main_frame.config(bg=self.border_color)
            if hasattr(self, 'separator'):
                self.separator.config(bg="#e2e8f0")
        
        self.main_frame.bind("<Enter>", on_enter)
        self.main_frame.bind("<Leave>", on_leave)
    
    def get_frame(self):
        """获取内容框架，用于添加子控件"""
        return self.content_frame
    
    def get_main_frame(self):
        """获取主框架，用于布局"""
        return self.main_frame
    
    def pack(self, **kwargs):
        """包装pack方法"""
        self.main_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """包装grid方法"""
        self.main_frame.grid(**kwargs)


class ResponsiveGrid:
    """响应式网格布局类 - 自动适应窗口大小的卡片网格"""
    
    def __init__(self, parent, min_card_width=350, max_columns=3, padding=10):
        self.parent = parent
        self.min_card_width = min_card_width
        self.max_columns = max_columns
        self.padding = padding
        self.cards = []
        
        # 创建容器
        self.container = tk.Frame(parent, bg="#f1f5f9")
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # 绑定窗口大小变化事件
        self.container.bind("<Configure>", self._on_resize)
    
    def add_card(self, card_frame):
        """添加卡片到网格"""
        self.cards.append(card_frame)
        self._layout_cards()
    
    def _on_resize(self, event=None):
        """窗口大小变化时重新布局"""
        self._layout_cards()
    
    def _layout_cards(self):
        """重新布局所有卡片"""
        if not self.cards:
            return
        
        # 计算可用宽度
        container_width = self.container.winfo_width()
        if container_width < 100:  # 初始宽度可能不正确
            container_width = self.container.winfo_reqwidth()
        
        # 计算列数
        available_width = container_width - (self.padding * 2)
        columns = max(1, min(self.max_columns, available_width // self.min_card_width))
        
        # 清除现有布局
        for card in self.cards:
            card.get_main_frame().pack_forget()
            card.get_main_frame().grid_forget()
        
        # 重新布局
        for idx, card in enumerate(self.cards):
            row = idx // columns
            col = idx % columns
            card.get_main_frame().grid(
                row=row, 
                column=col, 
                padx=self.padding, 
                pady=self.padding, 
                sticky="nsew"
            )
        
        # 配置列权重
        for col in range(columns):
            self.container.columnconfigure(col, weight=1)


class AdminPanelUI:
    """管理员面板UI类 - 封装所有管理员面板UI组件"""
    
    def __init__(self, parent, control_panel):
        self.parent = parent
        self.control_panel = control_panel
        
        # 创建主容器
        self.main_frame = tk.Frame(parent, bg="#f1f5f9")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动区域
        self._create_scrollable_area()
        
        # 创建快捷工具栏
        self._create_toolbar()
        
        # 创建响应式网格布局
        self.grid_layout = ResponsiveGrid(self.scroll_frame, min_card_width=400, max_columns=2)
        
        # 创建各个功能模块
        self._create_ban_management_module()
        self._create_mute_management_module()
        self._create_op_management_module()
        
        # 配置滚动区域
        self._configure_scroll_region()
    
    def _create_scrollable_area(self):
        """创建可滚动区域"""
        # 创建Canvas
        self.canvas = tk.Canvas(self.main_frame, bg="#f1f5f9", highlightthickness=0)
        
        # 创建滚动条
        self.v_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        # 配置Canvas
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)
        
        # 布局
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建滚动框架
        self.scroll_frame = tk.Frame(self.canvas, bg="#f1f5f9")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_frame, anchor=tk.NW)
        
        # 绑定事件
        self.scroll_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # 绑定鼠标滚轮
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            scroll_delta = int(-1 * (event.delta / 120))
            self.canvas.yview_scroll(scroll_delta, "units")
            return "break"
        
        def _on_mousewheel_linux(event):
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
            return "break"
        
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
        self.canvas.bind("<Button-4>", _on_mousewheel_linux)
        self.canvas.bind("<Button-5>", _on_mousewheel_linux)
        self.scroll_frame.bind("<MouseWheel>", _on_mousewheel)
        self.scroll_frame.bind("<Button-4>", _on_mousewheel_linux)
        self.scroll_frame.bind("<Button-5>", _on_mousewheel_linux)
    
    def _on_frame_configure(self, event=None):
        """框架大小变化时更新滚动区域"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """Canvas大小变化时更新窗口宽度"""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _configure_scroll_region(self):
        """配置滚动区域"""
        self.scroll_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _create_toolbar(self):
        """创建快捷操作工具栏"""
        toolbar_card = CardFrame(self.scroll_frame, title="快捷操作", padding="10")
        toolbar_card.pack(fill=tk.X, padx=10, pady=10)
        
        toolbar_frame = toolbar_card.get_frame()
        
        # 快捷封禁按钮组
        ban_label = tk.Label(toolbar_frame, text="快捷封禁:", font=('微软雅黑', 9), bg="#ffffff", fg="#64748b")
        ban_label.pack(side=tk.LEFT, padx=(0, 10))
        
        quick_bans = [
            ("1小时", "1h"),
            ("1天", "1d"),
            ("7天", "7d"),
            ("永久", "perm")
        ]
        
        for text, duration in quick_bans:
            btn = ttk.Button(toolbar_frame, text=text, width=8,
                           command=lambda d=duration: self._quick_ban(d))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 分隔线
        separator = tk.Frame(toolbar_frame, width=2, bg="#e2e8f0")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=15)
        
        # 快捷禁言按钮组
        mute_label = tk.Label(toolbar_frame, text="快捷禁言:", font=('微软雅黑', 9), bg="#ffffff", fg="#64748b")
        mute_label.pack(side=tk.LEFT, padx=(0, 10))
        
        quick_mutes = [
            ("30分钟", "30m"),
            ("2小时", "2h"),
            ("1天", "1d")
        ]
        
        for text, duration in quick_mutes:
            btn = ttk.Button(toolbar_frame, text=text, width=8,
                           command=lambda d=duration: self._quick_mute(d))
            btn.pack(side=tk.LEFT, padx=2)
        
        # 全局搜索框
        search_label = tk.Label(toolbar_frame, text="搜索:", font=('微软雅黑', 9), bg="#ffffff", fg="#64748b")
        search_label.pack(side=tk.LEFT, padx=(30, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind('<KeyRelease>', self._on_search)
    
    def _create_ban_management_module(self):
        """创建封禁管理模块"""
        # 封禁操作卡片
        ban_action_card = CardFrame(self.grid_layout.container, title="封禁管理", padding="15")
        
        ban_frame = ban_action_card.get_frame()
        
        # 玩家选择
        player_frame = tk.Frame(ban_frame, bg="#ffffff")
        player_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(player_frame, text="玩家:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT)
        self.ban_player_var = tk.StringVar()
        self.ban_player_combo = ttk.Combobox(player_frame, textvariable=self.ban_player_var, width=20)
        self.ban_player_combo.pack(side=tk.LEFT, padx=5)
        
        # 封禁类型
        tk.Label(player_frame, text="类型:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT, padx=(15, 0))
        self.ban_type_var = tk.StringVar(value="临时")
        ban_type_combo = ttk.Combobox(player_frame, textvariable=self.ban_type_var, 
                                     values=["临时", "永久"], width=10, state="readonly")
        ban_type_combo.pack(side=tk.LEFT, padx=5)
        
        # 时间选择
        tk.Label(player_frame, text="时间:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT, padx=(15, 0))
        self.ban_time_var = tk.StringVar(value="1h")
        self.ban_time_combo = ttk.Combobox(player_frame, textvariable=self.ban_time_var,
                                          values=["1h", "2h", "6h", "12h", "1d", "7d", "30d"],
                                          width=10, state="readonly")
        self.ban_time_combo.pack(side=tk.LEFT, padx=5)
        
        # 原因输入
        reason_frame = tk.Frame(ban_frame, bg="#ffffff")
        reason_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(reason_frame, text="原因:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT)
        self.ban_reason_var = tk.StringVar(value="违反服务器规则")
        ban_reason_entry = ttk.Entry(reason_frame, textvariable=self.ban_reason_var, width=40)
        ban_reason_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 操作按钮
        btn_frame = tk.Frame(ban_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X)
        
        ban_btn = ttk.Button(btn_frame, text="封禁玩家", command=self._ban_player, width=12)
        ban_btn.pack(side=tk.LEFT, padx=2)
        
        unban_btn = ttk.Button(btn_frame, text="解除封禁", command=self._unban_player, width=12)
        unban_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = ttk.Button(btn_frame, text="刷新列表", command=self._refresh_ban_list, width=12)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # 添加到网格
        self.grid_layout.add_card(ban_action_card)
        
        # 封禁列表卡片
        ban_list_card = CardFrame(self.grid_layout.container, title="封禁列表", padding="15")
        
        list_frame = ban_list_card.get_frame()
        
        # 创建树形视图
        columns = ("玩家", "原因", "类型", "剩余时间", "状态")
        self.ban_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.ban_tree.heading(col, text=col)
            if col == "玩家":
                self.ban_tree.column(col, width=120)
            elif col == "原因":
                self.ban_tree.column(col, width=150)
            elif col == "类型":
                self.ban_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == "剩余时间":
                self.ban_tree.column(col, width=100, anchor=tk.CENTER)
            else:
                self.ban_tree.column(col, width=60, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.ban_tree.yview)
        self.ban_tree.configure(yscrollcommand=scrollbar.set)
        
        self.ban_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 批量操作按钮
        batch_frame = tk.Frame(list_frame, bg="#ffffff")
        batch_frame.pack(fill=tk.X, pady=(10, 0))
        
        batch_unban_btn = ttk.Button(batch_frame, text="批量解封", command=self._batch_unban)
        batch_unban_btn.pack(side=tk.LEFT, padx=2)
        
        batch_update_btn = ttk.Button(batch_frame, text="批量更新", command=self._batch_update_ban)
        batch_update_btn.pack(side=tk.LEFT, padx=2)
        
        self.grid_layout.add_card(ban_list_card)
    
    def _create_mute_management_module(self):
        """创建禁言管理模块"""
        # 禁言操作卡片
        mute_action_card = CardFrame(self.grid_layout.container, title="禁言管理", padding="15")
        
        mute_frame = mute_action_card.get_frame()
        
        # 玩家选择
        player_frame = tk.Frame(mute_frame, bg="#ffffff")
        player_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(player_frame, text="玩家:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT)
        self.mute_player_var = tk.StringVar()
        self.mute_player_combo = ttk.Combobox(player_frame, textvariable=self.mute_player_var, width=20)
        self.mute_player_combo.pack(side=tk.LEFT, padx=5)
        
        # 禁言类型
        tk.Label(player_frame, text="类型:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT, padx=(15, 0))
        self.mute_type_var = tk.StringVar(value="临时")
        mute_type_combo = ttk.Combobox(player_frame, textvariable=self.mute_type_var,
                                      values=["临时", "永久"], width=10, state="readonly")
        mute_type_combo.pack(side=tk.LEFT, padx=5)
        
        # 时间选择
        tk.Label(player_frame, text="时间:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT, padx=(15, 0))
        self.mute_time_var = tk.StringVar(value="1h")
        self.mute_time_combo = ttk.Combobox(player_frame, textvariable=self.mute_time_var,
                                           values=["30m", "1h", "2h", "6h", "12h", "1d", "7d"],
                                           width=10, state="readonly")
        self.mute_time_combo.pack(side=tk.LEFT, padx=5)
        
        # 原因输入
        reason_frame = tk.Frame(mute_frame, bg="#ffffff")
        reason_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(reason_frame, text="原因:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT)
        self.mute_reason_var = tk.StringVar(value="不当言论")
        mute_reason_entry = ttk.Entry(reason_frame, textvariable=self.mute_reason_var, width=40)
        mute_reason_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 操作按钮
        btn_frame = tk.Frame(mute_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X)
        
        mute_btn = ttk.Button(btn_frame, text="禁言玩家", command=self._mute_player, width=12)
        mute_btn.pack(side=tk.LEFT, padx=2)
        
        unmute_btn = ttk.Button(btn_frame, text="解除禁言", command=self._unmute_player, width=12)
        unmute_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = ttk.Button(btn_frame, text="刷新列表", command=self._refresh_mute_list, width=12)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.grid_layout.add_card(mute_action_card)
        
        # 禁言列表卡片
        mute_list_card = CardFrame(self.grid_layout.container, title="禁言列表", padding="15")
        
        list_frame = mute_list_card.get_frame()
        
        # 创建树形视图
        columns = ("玩家", "原因", "类型", "剩余时间", "状态")
        self.mute_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.mute_tree.heading(col, text=col)
            if col == "玩家":
                self.mute_tree.column(col, width=120)
            elif col == "原因":
                self.mute_tree.column(col, width=150)
            elif col == "类型":
                self.mute_tree.column(col, width=60, anchor=tk.CENTER)
            elif col == "剩余时间":
                self.mute_tree.column(col, width=100, anchor=tk.CENTER)
            else:
                self.mute_tree.column(col, width=60, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.mute_tree.yview)
        self.mute_tree.configure(yscrollcommand=scrollbar.set)
        
        self.mute_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 批量操作按钮
        batch_frame = tk.Frame(list_frame, bg="#ffffff")
        batch_frame.pack(fill=tk.X, pady=(10, 0))
        
        batch_unmute_btn = ttk.Button(batch_frame, text="批量解除", command=self._batch_unmute)
        batch_unmute_btn.pack(side=tk.LEFT, padx=2)
        
        batch_update_btn = ttk.Button(batch_frame, text="批量更新", command=self._batch_update_mute)
        batch_update_btn.pack(side=tk.LEFT, padx=2)
        
        self.grid_layout.add_card(mute_list_card)
    
    def _create_op_management_module(self):
        """创建管理员管理模块"""
        # 管理员操作卡片
        op_action_card = CardFrame(self.grid_layout.container, title="管理员管理", padding="15")
        
        op_frame = op_action_card.get_frame()
        
        # 权限等级说明按钮
        help_frame = tk.Frame(op_frame, bg="#ffffff")
        help_frame.pack(fill=tk.X, pady=(0, 5))
        
        help_btn = ttk.Button(help_frame, text="📖 权限等级说明", command=self._show_op_level_help, width=15)
        help_btn.pack(side=tk.RIGHT)
        
        # 玩家选择
        player_frame = tk.Frame(op_frame, bg="#ffffff")
        player_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(player_frame, text="玩家:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT)
        self.op_player_var = tk.StringVar()
        self.op_player_combo = ttk.Combobox(player_frame, textvariable=self.op_player_var, width=25)
        self.op_player_combo.pack(side=tk.LEFT, padx=5)
        
        # 权限等级
        tk.Label(player_frame, text="权限:", font=('微软雅黑', 10), bg="#ffffff", fg="#1e293b").pack(side=tk.LEFT, padx=(15, 0))
        self.op_level_var = tk.StringVar(value="4")
        op_level_combo = ttk.Combobox(player_frame, textvariable=self.op_level_var,
                                     values=["1", "2", "3", "4"], width=8, state="readonly")
        op_level_combo.pack(side=tk.LEFT, padx=5)
        
        # 权限等级简要说明
        level_desc_frame = tk.Frame(op_frame, bg="#f8fafc", padx=10, pady=5)
        level_desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.level_desc_label = tk.Label(
            level_desc_frame, 
            text="等级4: 完全权限 - 可以执行所有命令包括停止服务器",
            font=('微软雅黑', 9),
            bg="#f8fafc",
            fg="#64748b",
            wraplength=400,
            justify=tk.LEFT
        )
        self.level_desc_label.pack(fill=tk.X)
        
        # 绑定权限等级变化事件
        op_level_combo.bind('<<ComboboxSelected>>', self._on_op_level_changed)
        
        # 操作按钮
        btn_frame = tk.Frame(op_frame, bg="#ffffff")
        btn_frame.pack(fill=tk.X)
        
        add_op_btn = ttk.Button(btn_frame, text="设为管理员", command=self._add_op, width=12)
        add_op_btn.pack(side=tk.LEFT, padx=2)
        
        remove_op_btn = ttk.Button(btn_frame, text="取消管理员", command=self._remove_op, width=12)
        remove_op_btn.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = ttk.Button(btn_frame, text="刷新列表", command=self._refresh_op_list, width=12)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        self.grid_layout.add_card(op_action_card)
        
        # 管理员列表卡片
        op_list_card = CardFrame(self.grid_layout.container, title="管理员列表", padding="15")
        
        list_frame = op_list_card.get_frame()
        
        # 创建树形视图
        columns = ("玩家", "权限等级", "添加时间", "状态")
        self.op_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.op_tree.heading(col, text=col)
            if col == "玩家":
                self.op_tree.column(col, width=120)
            elif col == "权限等级":
                self.op_tree.column(col, width=80, anchor=tk.CENTER)
            elif col == "添加时间":
                self.op_tree.column(col, width=120, anchor=tk.CENTER)
            else:
                self.op_tree.column(col, width=60, anchor=tk.CENTER)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.op_tree.yview)
        self.op_tree.configure(yscrollcommand=scrollbar.set)
        
        self.op_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 批量操作按钮
        batch_frame = tk.Frame(list_frame, bg="#ffffff")
        batch_frame.pack(fill=tk.X, pady=(10, 0))
        
        batch_remove_btn = ttk.Button(batch_frame, text="批量移除", command=self._batch_remove_op)
        batch_remove_btn.pack(side=tk.LEFT, padx=2)
        
        batch_update_btn = ttk.Button(batch_frame, text="批量更新权限", command=self._batch_update_op)
        batch_update_btn.pack(side=tk.LEFT, padx=2)
        
        self.grid_layout.add_card(op_list_card)
    
    # ========== 回调方法（需要由控制面板实现）==========
    
    def _quick_ban(self, duration):
        """快捷封禁"""
        if hasattr(self.control_panel, 'quick_ban'):
            self.control_panel.quick_ban(duration)
    
    def _quick_mute(self, duration):
        """快捷禁言"""
        if hasattr(self.control_panel, 'quick_mute'):
            self.control_panel.quick_mute(duration)
    
    def _on_search(self, event):
        """搜索事件"""
        search_text = self.search_var.get()
        if hasattr(self.control_panel, 'search_players'):
            self.control_panel.search_players(search_text)
    
    def _ban_player(self):
        """封禁玩家"""
        if hasattr(self.control_panel, 'ban_player'):
            self.control_panel.ban_player()
    
    def _unban_player(self):
        """解除封禁"""
        if hasattr(self.control_panel, 'pardon_player'):
            self.control_panel.pardon_player()
    
    def _refresh_ban_list(self):
        """刷新封禁列表"""
        if hasattr(self.control_panel, 'load_banned_players'):
            self.control_panel.load_banned_players()
    
    def _batch_unban(self):
        """批量解封"""
        if hasattr(self.control_panel, 'batch_remove_ops'):
            self.control_panel.batch_pardon()
    
    def _batch_update_ban(self):
        """批量更新封禁"""
        if hasattr(self.control_panel, 'update_ban_times'):
            self.control_panel.update_ban_times()
    
    def _mute_player(self):
        """禁言玩家"""
        if hasattr(self.control_panel, 'mute_player'):
            self.control_panel.mute_player()
    
    def _unmute_player(self):
        """解除禁言"""
        if hasattr(self.control_panel, 'unmute_player'):
            self.control_panel.unmute_player()
    
    def _refresh_mute_list(self):
        """刷新禁言列表"""
        if hasattr(self.control_panel, 'load_muted_players'):
            self.control_panel.load_muted_players()
    
    def _batch_unmute(self):
        """批量解除禁言"""
        if hasattr(self.control_panel, 'batch_unmute'):
            self.control_panel.batch_unmute()
    
    def _batch_update_mute(self):
        """批量更新禁言"""
        if hasattr(self.control_panel, 'update_mute_times'):
            self.control_panel.update_mute_times()
    
    def _add_op(self):
        """添加管理员"""
        if hasattr(self.control_panel, 'add_op'):
            self.control_panel.add_op()
    
    def _remove_op(self):
        """移除管理员"""
        if hasattr(self.control_panel, 'remove_op'):
            self.control_panel.remove_op()
    
    def _refresh_op_list(self):
        """刷新管理员列表"""
        if hasattr(self.control_panel, 'load_ops'):
            self.control_panel.load_ops()
    
    def _batch_remove_op(self):
        """批量移除管理员"""
        if hasattr(self.control_panel, 'batch_remove_ops'):
            self.control_panel.batch_remove_ops()
    
    def _batch_update_op(self):
        """批量更新管理员权限"""
        if hasattr(self.control_panel, 'batch_update_op_levels'):
            self.control_panel.batch_update_op_levels()
    
    def _on_op_level_changed(self, event=None):
        """权限等级改变时更新说明文字"""
        level = self.op_level_var.get()
        descriptions = {
            "1": "等级1: 基础管理员 - 只能踢人/封禁/解封，适合普通管理员",
            "2": "等级2: 中级管理员 - 可以改游戏模式、传送、给予物品等",
            "3": "等级3: 高级管理员 - 可以停服、保存世界、管理白名单",
            "4": "等级4: 完全权限 - 可以执行所有命令包括重载配置"
        }
        self.level_desc_label.config(text=descriptions.get(level, ""))
    
    def _show_op_level_help(self):
        """显示权限等级详细说明"""
        help_window = tk.Toplevel(self.parent)
        help_window.title("管理员权限等级说明")
        help_window.geometry("600x500")
        help_window.configure(bg="#ffffff")
        
        # 创建滚动区域
        canvas = tk.Canvas(help_window, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(help_window, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#ffffff", padx=20, pady=20)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        
        # 标题
        title = tk.Label(
            scroll_frame,
            text="📋 Minecraft 服务器管理员权限等级详解",
            font=('微软雅黑', 14, 'bold'),
            bg="#ffffff",
            fg="#1e293b"
        )
        title.pack(pady=(0, 20))
        
        # 权限等级说明
        levels = [
            {
                "title": "等级 1 - 基础管理员",
                "color": "#22c55e",
                "commands": [
                    "• /kick - 踢出玩家",
                    "• /ban - 封禁玩家",
                    "• /pardon - 解除封禁",
                    "• /ban-ip - IP封禁",
                    "• /pardon-ip - 解除IP封禁",
                    "• /op - 给予管理员权限",
                    "• /deop - 移除管理员权限"
                ],
                "desc": "适用场景：普通管理员，负责玩家管理和基础封禁操作"
            },
            {
                "title": "等级 2 - 中级管理员",
                "color": "#3b82f6",
                "commands": [
                    "包含等级1的所有权限，额外增加：",
                    "• /gamemode - 更改游戏模式",
                    "• /difficulty - 更改游戏难度",
                    "• /weather - 更改天气",
                    "• /time - 更改时间",
                    "• /tp - 传送玩家",
                    "• /give - 给予物品",
                    "• /effect - 给予/移除效果",
                    "• /clear - 清空玩家背包"
                ],
                "desc": "适用场景：高级管理员，可以管理游戏环境和玩家状态"
            },
            {
                "title": "等级 3 - 高级管理员",
                "color": "#f59e0b",
                "commands": [
                    "包含等级1-2的所有权限，额外增加：",
                    "• /stop - 停止服务器",
                    "• /save-all - 保存世界",
                    "• /save-off - 关闭自动保存",
                    "• /save-on - 开启自动保存",
                    "• /whitelist - 管理白名单",
                    "• /seed - 查看世界种子",
                    "• /publish - 开放局域网"
                ],
                "desc": "适用场景：服务器管理员，可以管理服务器运行状态"
            },
            {
                "title": "等级 4 - 完全权限（服主级别）",
                "color": "#ef4444",
                "commands": [
                    "包含等级1-3的所有权限，额外增加：",
                    "• /reload - 重新加载服务器配置",
                    "• /defaultgamemode - 设置默认游戏模式",
                    "• /setworldspawn - 设置世界出生点",
                    "• /worldborder - 管理世界边界",
                    "• /scoreboard - 管理计分板",
                    "• /datapack - 管理数据包",
                    "• /advancement - 管理玩家成就",
                    "• 以及所有其他高级命令"
                ],
                "desc": "适用场景：服务器所有者，拥有服务器的完全控制权"
            }
        ]
        
        for level in levels:
            # 等级标题
            level_title = tk.Label(
                scroll_frame,
                text=level["title"],
                font=('微软雅黑', 12, 'bold'),
                bg="#ffffff",
                fg=level["color"]
            )
            level_title.pack(anchor=tk.W, pady=(15, 5))
            
            # 命令列表
            for cmd in level["commands"]:
                cmd_label = tk.Label(
                    scroll_frame,
                    text=cmd,
                    font=('微软雅黑', 10),
                    bg="#ffffff",
                    fg="#475569"
                )
                cmd_label.pack(anchor=tk.W, padx=20)
            
            # 适用场景
            desc_label = tk.Label(
                scroll_frame,
                text=level["desc"],
                font=('微软雅黑', 9, 'italic'),
                bg="#ffffff",
                fg="#64748b"
            )
            desc_label.pack(anchor=tk.W, padx=20, pady=(5, 0))
        
        # 安全提示
        warning_frame = tk.Frame(scroll_frame, bg="#fef3c7", padx=15, pady=15)
        warning_frame.pack(fill=tk.X, pady=(20, 0))
        
        warning_title = tk.Label(
            warning_frame,
            text="⚠️ 安全提示",
            font=('微软雅黑', 11, 'bold'),
            bg="#fef3c7",
            fg="#92400e"
        )
        warning_title.pack(anchor=tk.W)
        
        warning_text = tk.Label(
            warning_frame,
            text="建议只给信任的人分配等级3-4的权限，特别是等级4可以执行停止服务器、\n重载配置等关键操作，请谨慎分配！",
            font=('微软雅黑', 9),
            bg="#fef3c7",
            fg="#92400e",
            justify=tk.LEFT
        )
        warning_text.pack(anchor=tk.W, pady=(5, 0))
        
        # 关闭按钮
        close_btn = ttk.Button(scroll_frame, text="关闭", command=help_window.destroy, width=15)
        close_btn.pack(pady=(20, 0))
        
        # 更新滚动区域
        scroll_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    # ========== 公共方法 ==========
    
    def get_frame(self):
        """获取主框架"""
        return self.main_frame
    
    def update_ban_list(self, ban_list):
        """更新封禁列表"""
        # 清空现有数据
        for item in self.ban_tree.get_children():
            self.ban_tree.delete(item)
        
        # 添加新数据
        for ban in ban_list:
            self.ban_tree.insert("", tk.END, values=(
                ban.get("player", ""),
                ban.get("reason", ""),
                ban.get("type", ""),
                ban.get("remaining", ""),
                ban.get("status", "")
            ))
    
    def update_mute_list(self, mute_list):
        """更新禁言列表"""
        for item in self.mute_tree.get_children():
            self.mute_tree.delete(item)
        
        for mute in mute_list:
            self.mute_tree.insert("", tk.END, values=(
                mute.get("player", ""),
                mute.get("reason", ""),
                mute.get("type", ""),
                mute.get("remaining", ""),
                mute.get("status", "")
            ))
    
    def update_op_list(self, op_list):
        """更新管理员列表"""
        for item in self.op_tree.get_children():
            self.op_tree.delete(item)
        
        for op in op_list:
            self.op_tree.insert("", tk.END, values=(
                op.get("player", ""),
                op.get("level", ""),
                op.get("added_time", ""),
                op.get("status", "")
            ))
