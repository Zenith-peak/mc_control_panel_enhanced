import tkinter as tk
from tkinter import ttk


class UIStyles:
    """UI样式管理器"""
    
    def __init__(self):
        # 主色调：现代蓝色系
        self.primary_color = "#3b82f6"
        self.primary_hover = "#2563eb"
        self.primary_light = "#dbeafe"
        
        # 辅助色：协调的绿色和红色
        self.secondary_color = "#10b981"
        self.secondary_hover = "#059669"
        self.secondary_light = "#d1fae5"
        self.accent_color = "#ef4444"
        self.accent_hover = "#dc2626"
        self.accent_light = "#fee2e2"
        
        # 背景色：柔和的现代灰色调
        self.background_color = "#f1f5f9"
        self.card_color = "#ffffff"
        self.surface_color = "#f8fafc"
        
        # 文本色：良好的对比度
        self.text_color = "#1e293b"
        self.text_secondary = "#64748b"
        self.text_muted = "#94a3b8"
        
        # 边框色：更细的边框颜色
        self.border_color = "#e2e8f0"
        self.border_light = "#f1f5f9"
        self.divider_color = "#cbd5e1"
    
    def apply_styles(self):
        style = ttk.Style()
        
        # 统一字体配置 - 优化中文字体显示
        font_family = '微软雅黑'
        # 字体大小定义 - 针对不同分辨率优化
        font_size_small = 9      # 小字：工具提示、辅助信息
        font_size_normal = 10    # 正文：按钮、标签、输入框
        font_size_large = 11     # 较大：框架标题、重要标签
        font_size_title = 13     # 标题：窗口标题、大标题
        font_size_header = 14    # 页眉：状态显示、重要数值
        
        # 统一圆角半径
        corner_radius = 6
        
        # 统一内边距
        padding_small = [8, 4]
        padding_normal = [12, 8]
        padding_large = [16, 10]
        
        # 统一边框宽度
        border_width_normal = 1
        border_width_focus = 2
        
        # ===== TFrame 样式 =====
        style.configure("TFrame", background=self.background_color)
        
        # ===== TNotebook 样式 =====
        style.configure("TNotebook", 
                       background=self.background_color, 
                       borderwidth=border_width_normal, 
                       relief="flat",
                       tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", 
                       padding=padding_large, 
                       font=(font_family, font_size_normal, 'normal'),
                       borderwidth=border_width_normal,
                       relief="flat")
        style.map("TNotebook.Tab", 
                 background=[("selected", self.card_color), ("!selected", self.background_color)],
                 foreground=[("selected", self.primary_color), ("!selected", self.text_secondary)],
                 font=[("selected", (font_family, font_size_normal, 'bold')), ("!selected", (font_family, font_size_normal, 'normal'))],
                 relief=[("selected", "solid"), ("!selected", "flat")],
                 bordercolor=[("selected", self.primary_color), ("!selected", self.border_color)])
        
        # ===== TButton 样式 - 统一按钮样式 =====
        style.configure("TButton", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       borderwidth=0,
                       relief="flat",
                       background=self.primary_color,
                       foreground="white")
        style.map("TButton", 
                 background=[
                     ("active", self.primary_hover), 
                     ("pressed", self.primary_color), 
                     ("!active", self.primary_color),
                     ("hover", self.primary_hover),
                     ("!hover", self.primary_color)
                 ],
                 foreground=[
                     ("active", "white"), 
                     ("pressed", "white"), 
                     ("!active", "white"),
                     ("hover", "white"),
                     ("!hover", "white")
                 ],
                 relief=[("pressed", "flat"), ("!pressed", "flat"), ("hover", "flat"), ("!hover", "flat")],
                 font=[("hover", (font_family, font_size_normal, 'bold')), ("!hover", (font_family, font_size_normal))])
        
        # 次要按钮样式
        style.configure("Secondary.TButton", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       borderwidth=0,
                       relief="flat",
                       background=self.secondary_color,
                       foreground="white")
        style.map("Secondary.TButton", 
                 background=[
                     ("active", self.secondary_hover), 
                     ("pressed", self.secondary_color), 
                     ("!active", self.secondary_color),
                     ("hover", self.secondary_hover),
                     ("!hover", self.secondary_color)
                 ],
                 foreground=[
                     ("active", "white"), 
                     ("pressed", "white"), 
                     ("!active", "white"),
                     ("hover", "white"),
                     ("!hover", "white")
                 ],
                 font=[("hover", (font_family, font_size_normal, 'bold')), ("!hover", (font_family, font_size_normal))])
        
        # 危险/删除按钮样式
        style.configure("Danger.TButton", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       borderwidth=0,
                       relief="flat",
                       background=self.accent_color,
                       foreground="white")
        style.map("Danger.TButton", 
                 background=[
                     ("active", self.accent_hover), 
                     ("pressed", self.accent_color), 
                     ("!active", self.accent_color),
                     ("hover", self.accent_hover),
                     ("!hover", self.accent_color)
                 ],
                 foreground=[
                     ("active", "white"), 
                     ("pressed", "white"), 
                     ("!active", "white"),
                     ("hover", "white"),
                     ("!hover", "white")
                 ],
                 font=[("hover", (font_family, font_size_normal, 'bold')), ("!hover", (font_family, font_size_normal))])
        
        # 工具栏按钮样式（较小）
        style.configure("Toolbar.TButton", 
                       padding=padding_small, 
                       font=(font_family, font_size_small),
                       borderwidth=0,
                       relief="flat",
                       background=self.surface_color,
                       foreground=self.text_color)
        style.map("Toolbar.TButton", 
                 background=[
                     ("active", self.primary_light), 
                     ("pressed", self.primary_color), 
                     ("!active", self.surface_color),
                     ("hover", self.primary_light),
                     ("!hover", self.surface_color)
                 ],
                 foreground=[
                     ("active", self.primary_color), 
                     ("pressed", "white"), 
                     ("!active", self.text_color),
                     ("hover", self.primary_color),
                     ("!hover", self.text_color)
                 ],
                 font=[("hover", (font_family, font_size_small, 'bold')), ("!hover", (font_family, font_size_small))])
        
        # 轮廓按钮样式
        style.configure("Outline.TButton",
                       padding=padding_normal,
                       font=(font_family, font_size_normal),
                       borderwidth=1,
                       relief="solid",
                       background=self.card_color,
                       foreground=self.primary_color)
        style.map("Outline.TButton",
                 background=[
                     ("active", self.primary_light),
                     ("pressed", self.primary_color),
                     ("!active", self.card_color),
                     ("hover", self.primary_light),
                     ("!hover", self.card_color)
                 ],
                 foreground=[
                     ("active", self.primary_color),
                     ("pressed", "white"),
                     ("!active", self.primary_color),
                     ("hover", self.primary_hover),
                     ("!hover", self.primary_color)
                 ],
                 bordercolor=[
                     ("active", self.primary_color),
                     ("pressed", self.primary_color),
                     ("!active", self.primary_color),
                     ("hover", self.primary_hover),
                     ("!hover", self.primary_color)
                 ],
                 font=[("hover", (font_family, font_size_normal, 'bold')), ("!hover", (font_family, font_size_normal))])
        
        # 幽灵按钮样式（透明背景）
        style.configure("Ghost.TButton",
                       padding=padding_normal,
                       font=(font_family, font_size_normal),
                       borderwidth=0,
                       relief="flat",
                       background=self.background_color,
                       foreground=self.text_secondary)
        style.map("Ghost.TButton",
                 background=[
                     ("active", self.surface_color),
                     ("pressed", self.primary_light),
                     ("!active", self.background_color),
                     ("hover", self.surface_color),
                     ("!hover", self.background_color)
                 ],
                 foreground=[
                     ("active", self.primary_color),
                     ("pressed", self.primary_color),
                     ("!active", self.text_secondary),
                     ("hover", self.primary_color),
                     ("!hover", self.text_secondary)
                 ],
                 font=[("hover", (font_family, font_size_normal, 'bold')), ("!hover", (font_family, font_size_normal))])
        
        # ===== TLabel 样式 - 统一标签样式 =====
        style.configure("TLabel", 
                       background=self.background_color, 
                       font=(font_family, font_size_normal), 
                       foreground=self.text_color)
        
        # 标题标签
        style.configure("Title.TLabel", 
                       background=self.background_color, 
                       font=(font_family, font_size_title, 'bold'), 
                       foreground=self.text_color)
        
        # 副标题标签
        style.configure("Subtitle.TLabel", 
                       background=self.background_color, 
                       font=(font_family, font_size_large), 
                       foreground=self.text_secondary)
        
        # 强调标签
        style.configure("Accent.TLabel", 
                       background=self.background_color, 
                       font=(font_family, font_size_normal, 'bold'), 
                       foreground=self.primary_color)
        
        # ===== TEntry 样式 - 统一输入框样式 =====
        style.configure("TEntry", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       borderwidth=border_width_normal,
                       relief="solid",
                       background=self.card_color,
                       foreground=self.text_color,
                       fieldbackground=self.card_color)
        style.map("TEntry", 
                 bordercolor=[("focus", self.primary_color), ("!focus", self.border_color)],
                 relief=[("focus", "solid"), ("!focus", "solid")],
                 fieldbackground=[("focus", self.card_color), ("!focus", self.card_color)],
                 selectbackground=[("!focus", self.primary_light), ("focus", self.primary_color)],
                 selectforeground=[("!focus", self.text_color), ("focus", "white")])
        
        # 只读输入框
        style.configure("Readonly.TEntry", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       borderwidth=border_width_normal,
                       relief="solid",
                       background=self.surface_color,
                       foreground=self.text_secondary,
                       fieldbackground=self.surface_color)
        
        # ===== TLabelframe 样式 - 统一标签框架样式 =====
        style.configure("TLabelframe", 
                       background=self.background_color, 
                       borderwidth=border_width_normal, 
                       relief="solid",
                       bordercolor=self.border_color)
        style.configure("TLabelframe.Label", 
                       background=self.background_color, 
                       font=(font_family, font_size_large, 'bold'),
                       foreground=self.primary_color,
                       padding=[8, 4])
        style.map("TLabelframe",
                 bordercolor=[("hover", self.primary_color), ("!hover", self.border_color)],
                 relief=[("hover", "solid"), ("!hover", "solid")],
                 borderwidth=[("hover", border_width_focus), ("!hover", border_width_normal)])
        
        # 卡片式标签框架
        style.configure("Card.TLabelframe", 
                       background=self.card_color, 
                       borderwidth=border_width_normal, 
                       relief="solid",
                       bordercolor=self.border_color)
        style.configure("Card.TLabelframe.Label", 
                       background=self.card_color, 
                       font=(font_family, font_size_large, 'bold'),
                       foreground=self.text_color,
                       padding=[8, 4])
        style.map("Card.TLabelframe",
                 bordercolor=[("hover", self.primary_color), ("!hover", self.border_color)],
                 borderwidth=[("hover", border_width_focus), ("!hover", border_width_normal)])
        
        # 悬停高亮标签框架
        style.configure("Hover.TLabelframe",
                       background=self.card_color,
                       borderwidth=border_width_normal,
                       relief="solid",
                       bordercolor=self.border_color)
        style.configure("Hover.TLabelframe.Label",
                       background=self.card_color,
                       font=(font_family, font_size_large, 'bold'),
                       foreground=self.text_color,
                       padding=[8, 4])
        style.map("Hover.TLabelframe",
                 bordercolor=[("hover", self.primary_color), ("!hover", self.border_color)],
                 borderwidth=[("hover", border_width_focus), ("!hover", border_width_normal)])
        
        # ===== Treeview 样式 - 统一树形视图样式 =====
        # 根据字体大小调整行高，确保中文字符显示完整
        treeview_rowheight = 36  # 增加行高以适应中文字体
        style.configure("Treeview", 
                       background=self.card_color, 
                       font=(font_family, font_size_normal),
                       rowheight=treeview_rowheight,
                       fieldbackground=self.card_color,
                       foreground=self.text_color)
        style.configure("Treeview.Heading", 
                       background=self.surface_color, 
                       font=(font_family, font_size_normal, 'bold'),
                       padding=(12, 8),
                       relief="flat",
                       foreground=self.text_color)
        style.map("Treeview", 
                 background=[
                     ("selected", self.primary_color), 
                     ("!selected", self.card_color),
                     ("hover", self.primary_light)
                 ],
                 foreground=[
                     ("selected", "white"), 
                     ("!selected", self.text_color),
                     ("hover", self.text_color)
                 ],
                 fieldbackground=[
                     ("selected", self.primary_color), 
                     ("!selected", self.card_color),
                     ("hover", self.primary_light)
                 ])
        style.map("Treeview.Heading",
                 background=[("active", self.primary_light), ("!active", self.surface_color)],
                 foreground=[("active", self.primary_color), ("!active", self.text_color)])
        
        # Treeview 行悬停样式
        style.configure("Hover.Treeview",
                       background=self.card_color,
                       font=(font_family, font_size_normal),
                       rowheight=treeview_rowheight,
                       fieldbackground=self.card_color,
                       foreground=self.text_color)
        style.map("Hover.Treeview",
                 background=[
                     ("selected", self.primary_color),
                     ("!selected", self.card_color),
                     ("hover", self.primary_light)
                 ],
                 foreground=[
                     ("selected", "white"),
                     ("!selected", self.text_color),
                     ("hover", self.primary_color)
                 ])
        
        # ===== 滚动条样式 =====
        style.configure("Vertical.TScrollbar", 
                       background=self.surface_color,
                       borderwidth=0,
                       relief="flat",
                       arrowcolor=self.text_secondary,
                       troughcolor=self.background_color)
        style.map("Vertical.TScrollbar", 
                 background=[("active", self.primary_color), ("!active", self.surface_color)],
                 arrowcolor=[("active", "white"), ("!active", self.text_secondary)])
        
        style.configure("Horizontal.TScrollbar", 
                       background=self.surface_color,
                       borderwidth=0,
                       relief="flat",
                       arrowcolor=self.text_secondary,
                       troughcolor=self.background_color)
        style.map("Horizontal.TScrollbar", 
                 background=[("active", self.primary_color), ("!active", self.surface_color)],
                 arrowcolor=[("active", "white"), ("!active", self.text_secondary)])
        
        # ===== TCombobox 样式 =====
        style.configure("TCombobox", 
                       padding=padding_normal, 
                       font=(font_family, font_size_normal),
                       background=self.card_color,
                       foreground=self.text_color,
                       fieldbackground=self.card_color,
                       arrowcolor=self.primary_color)
        style.map("TCombobox",
                 fieldbackground=[("readonly", self.card_color), ("!readonly", self.card_color)],
                 selectbackground=[("!focus", self.primary_light), ("focus", self.primary_color)],
                 selectforeground=[("!focus", self.text_color), ("focus", "white")])
        
        # ===== TCheckbutton 样式 =====
        style.configure("TCheckbutton",
                       font=(font_family, font_size_normal),
                       background=self.background_color,
                       foreground=self.text_color)
        style.map("TCheckbutton",
                 background=[("active", self.background_color), ("!active", self.background_color)],
                 foreground=[("active", self.primary_color), ("!active", self.text_color)])
        
        # ===== TRadiobutton 样式 =====
        style.configure("TRadiobutton",
                       font=(font_family, font_size_normal),
                       background=self.background_color,
                       foreground=self.text_color)
        style.map("TRadiobutton",
                 background=[("active", self.background_color), ("!active", self.background_color)],
                 foreground=[("active", self.primary_color), ("!active", self.text_color)])
        
        # ===== TScale 样式 =====
        style.configure("TScale",
                       background=self.background_color,
                       troughcolor=self.surface_color,
                       borderwidth=0)
        style.map("TScale",
                 background=[("active", self.primary_color), ("!active", self.primary_color)])
        
        # ===== TProgressbar 样式 =====
        style.configure("TProgressbar",
                       background=self.primary_color,
                       troughcolor=self.surface_color,
                       borderwidth=0,
                       relief="flat")
        
        # 成功进度条
        style.configure("Success.Horizontal.TProgressbar",
                       background=self.secondary_color,
                       troughcolor=self.surface_color,
                       borderwidth=0,
                       relief="flat")
        
        # 警告进度条
        style.configure("Warning.Horizontal.TProgressbar",
                       background="#f59e0b",
                       troughcolor=self.surface_color,
                       borderwidth=0,
                       relief="flat")
        
        # 危险进度条
        style.configure("Danger.Horizontal.TProgressbar",
                       background=self.accent_color,
                       troughcolor=self.surface_color,
                       borderwidth=0,
                       relief="flat")
        
        # ===== TSeparator 样式 =====
        style.configure("TSeparator",
                       background=self.divider_color)
        
        # ===== TSpinbox 样式 =====
        style.configure("TSpinbox",
                       padding=padding_normal,
                       font=(font_family, font_size_normal),
                       background=self.card_color,
                       foreground=self.text_color,
                       fieldbackground=self.card_color,
                       arrowcolor=self.primary_color)
        style.map("TSpinbox",
                 bordercolor=[("focus", self.primary_color), ("!focus", self.border_color)],
                 fieldbackground=[("readonly", self.card_color), ("!readonly", self.card_color)])
        
        return style


class TooltipManager:
    """工具提示管理器 - 为控件添加悬停提示"""
    
    def __init__(self, widget, text, delay=500, bg_color="#2d3748", fg_color="#ffffff", 
                 border_color="#4a5568", font_size=10, padding=(8, 5)):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_color = border_color
        self.font_size = font_size
        self.padding = padding
        self.tooltip_window = None
        self.tooltip_id = None
        
        # 绑定事件
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)
        
    def _on_enter(self, event=None):
        """鼠标进入控件时显示工具提示"""
        self._schedule_tooltip()
        
    def _on_leave(self, event=None):
        """鼠标离开控件时隐藏工具提示"""
        self._unschedule_tooltip()
        self._hide_tooltip()
        
    def _schedule_tooltip(self):
        """延迟显示工具提示"""
        self.tooltip_id = self.widget.after(self.delay, self._show_tooltip)
        
    def _unschedule_tooltip(self):
        """取消延迟显示"""
        if self.tooltip_id:
            self.widget.after_cancel(self.tooltip_id)
            self.tooltip_id = None
            
    def _show_tooltip(self):
        """显示工具提示窗口"""
        if self.tooltip_window or not self.text:
            return
            
        # 获取控件位置
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # 创建工具提示窗口
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_attributes("-topmost", True)
        
        # 创建带圆角效果的标签
        frame = tk.Frame(
            self.tooltip_window,
            background=self.border_color,
            bd=1,
            relief="solid"
        )
        frame.pack()
        
        label = tk.Label(
            frame,
            text=self.text,
            background=self.bg_color,
            foreground=self.fg_color,
            font=("微软雅黑", self.font_size),
            padx=self.padding[0],
            pady=self.padding[1],
            justify="left",
            wraplength=300
        )
        label.pack()
        
        # 调整位置，确保不超出屏幕
        self.tooltip_window.update_idletasks()
        tooltip_width = self.tooltip_window.winfo_width()
        tooltip_height = self.tooltip_window.winfo_height()
        screen_width = self.tooltip_window.winfo_screenwidth()
        screen_height = self.tooltip_window.winfo_screenheight()
        
        # 水平居中
        x = x - tooltip_width // 2
        # 如果超出右边界，向左调整
        if x + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 10
        # 如果超出左边界，向右调整
        if x < 0:
            x = 10
            
        # 如果超出下边界，显示在控件上方
        if y + tooltip_height > screen_height:
            y = self.widget.winfo_rooty() - tooltip_height - 5
            
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
    def _hide_tooltip(self):
        """隐藏工具提示窗口"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
            
    def update_text(self, new_text):
        """更新工具提示文本"""
        self.text = new_text


def add_tooltip(widget, text, **kwargs):
    """
    为控件添加工具提示的便捷函数
    
    参数:
        widget: 要添加工具提示的控件
        text: 工具提示文本
        **kwargs: TooltipManager 的其他参数
    """
    return TooltipManager(widget, text, **kwargs)
