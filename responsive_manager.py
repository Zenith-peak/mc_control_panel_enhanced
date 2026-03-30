"""
屏幕适配管理器 - 负责处理Minecraft服务器控制面板的响应式布局
支持不同分辨率的自适应显示
"""
import tkinter as tk
from tkinter import ttk


class ResponsiveManager:
    """
    响应式布局管理器
    管理窗口大小变化时的自适应布局
    """
    
    # 屏幕尺寸断点
    BREAKPOINTS = {
        'xs': 800,    # 超小屏幕
        'sm': 1024,   # 小屏幕
        'md': 1280,   # 中等屏幕
        'lg': 1600,   # 大屏幕
        'xl': 1920    # 超大屏幕
    }
    
    # 最小窗口尺寸
    MIN_WIDTH = 800
    MIN_HEIGHT = 600
    
    def __init__(self, root):
        self.root = root
        self.current_width = 1000
        self.current_height = 700
        self.current_breakpoint = 'md'
        self.resize_callbacks = []
        self.layout_configs = {}
        
        # 绑定窗口大小变化事件
        self._bind_resize_event()
        
    def _bind_resize_event(self):
        """绑定窗口大小变化事件"""
        self.root.bind('<Configure>', self._on_window_configure)
        
    def _on_window_configure(self, event):
        """窗口大小变化时的回调"""
        if event.widget == self.root:
            new_width = event.width
            new_height = event.height
            
            # 只在尺寸变化超过阈值时更新
            if (abs(new_width - self.current_width) > 10 or 
                abs(new_height - self.current_height) > 10):
                self.current_width = new_width
                self.current_height = new_height
                self._update_breakpoint()
                self._notify_resize_callbacks()
                
    def _update_breakpoint(self):
        """更新当前屏幕尺寸断点"""
        width = self.current_width
        if width < self.BREAKPOINTS['xs']:
            self.current_breakpoint = 'xs'
        elif width < self.BREAKPOINTS['sm']:
            self.current_breakpoint = 'sm'
        elif width < self.BREAKPOINTS['md']:
            self.current_breakpoint = 'md'
        elif width < self.BREAKPOINTS['lg']:
            self.current_breakpoint = 'lg'
        else:
            self.current_breakpoint = 'xl'
            
    def _notify_resize_callbacks(self):
        """通知所有注册的回调函数"""
        for callback in self.resize_callbacks:
            try:
                callback(self.current_width, self.current_height, self.current_breakpoint)
            except Exception as e:
                print(f"Resize callback error: {e}")
                
    def add_resize_callback(self, callback):
        """添加窗口大小变化回调函数"""
        self.resize_callbacks.append(callback)
        
    def remove_resize_callback(self, callback):
        """移除窗口大小变化回调函数"""
        if callback in self.resize_callbacks:
            self.resize_callbacks.remove(callback)
            
    def get_current_breakpoint(self):
        """获取当前屏幕尺寸断点"""
        return self.current_breakpoint
        
    def get_current_size(self):
        """获取当前窗口尺寸"""
        return self.current_width, self.current_height
        
    def is_small_screen(self):
        """判断是否为小屏幕"""
        return self.current_breakpoint in ['xs', 'sm']
        
    def is_medium_screen(self):
        """判断是否为中等屏幕"""
        return self.current_breakpoint == 'md'
        
    def is_large_screen(self):
        """判断是否为大屏幕"""
        return self.current_breakpoint in ['lg', 'xl']
        
    def get_responsive_value(self, values_dict):
        """
        根据当前屏幕尺寸获取对应的值
        values_dict: {'xs': value1, 'sm': value2, 'md': value3, 'lg': value4, 'xl': value5}
        """
        if self.current_breakpoint in values_dict:
            return values_dict[self.current_breakpoint]
        # 如果当前断点没有定义，返回最近的定义
        breakpoints_order = ['xs', 'sm', 'md', 'lg', 'xl']
        current_idx = breakpoints_order.index(self.current_breakpoint)
        
        # 向前查找
        for i in range(current_idx, -1, -1):
            if breakpoints_order[i] in values_dict:
                return values_dict[breakpoints_order[i]]
                
        # 向后查找
        for i in range(current_idx, len(breakpoints_order)):
            if breakpoints_order[i] in values_dict:
                return values_dict[breakpoints_order[i]]
                
        return None


class ResponsiveGridLayout:
    """
    响应式网格布局管理器
    根据屏幕尺寸自动调整网格列数
    """
    
    def __init__(self, parent, responsive_manager):
        self.parent = parent
        self.responsive_manager = responsive_manager
        self.widgets = []
        self.current_columns = 4
        
    def add_widget(self, widget, **grid_options):
        """添加控件到网格布局"""
        self.widgets.append((widget, grid_options))
        self._update_layout()
        
    def _update_layout(self):
        """更新网格布局"""
        # 根据屏幕尺寸确定列数
        if self.responsive_manager.is_small_screen():
            columns = 2
        elif self.responsive_manager.is_medium_screen():
            columns = 3
        else:
            columns = 4
            
        if columns != self.current_columns:
            self.current_columns = columns
            self._rearrange_widgets()
            
    def _rearrange_widgets(self):
        """重新排列控件"""
        for idx, (widget, options) in enumerate(self.widgets):
            row = idx // self.current_columns
            col = idx % self.current_columns
            widget.grid(row=row, column=col, **options)
            
    def set_columns(self, columns):
        """手动设置列数"""
        if columns != self.current_columns:
            self.current_columns = columns
            self._rearrange_widgets()


class ResponsiveFrame(ttk.Frame):
    """
    响应式Frame类
    自动处理内部布局的响应式调整
    """
    
    def __init__(self, parent, responsive_manager, **kwargs):
        super().__init__(parent, **kwargs)
        self.responsive_manager = responsive_manager
        self.child_frames = []
        
        # 注册大小变化回调
        self.responsive_manager.add_resize_callback(self._on_resize)
        
    def _on_resize(self, width, height, breakpoint):
        """大小变化时的处理"""
        self._adjust_layout(breakpoint)
        
    def _adjust_layout(self, breakpoint):
        """调整布局 - 子类可以重写此方法"""
        pass
        
    def add_child_frame(self, frame):
        """添加子Frame"""
        self.child_frames.append(frame)
        
    def destroy(self):
        """销毁时清理"""
        self.responsive_manager.remove_resize_callback(self._on_resize)
        super().destroy()


class ResponsiveTreeview(ttk.Treeview):
    """
    响应式Treeview类
    根据屏幕尺寸自动调整列宽
    """
    
    def __init__(self, parent, responsive_manager, columns, **kwargs):
        super().__init__(parent, columns=columns, show="headings", **kwargs)
        self.responsive_manager = responsive_manager
        self.column_configs = {}
        
        # 注册大小变化回调
        self.responsive_manager.add_resize_callback(self._on_resize)
        
    def set_column_config(self, col_name, configs):
        """
        设置列的配置
        configs: {
            'xs': {'width': 50, 'stretch': False},
            'sm': {'width': 80, 'stretch': False},
            'md': {'width': 100, 'stretch': True},
            'lg': {'width': 120, 'stretch': True},
            'xl': {'width': 150, 'stretch': True}
        }
        """
        self.column_configs[col_name] = configs
        
    def _on_resize(self, width, height, breakpoint):
        """大小变化时调整列宽"""
        for col_name, configs in self.column_configs.items():
            if breakpoint in configs:
                config = configs[breakpoint]
                self.column(col_name, **config)
                
    def destroy(self):
        """销毁时清理"""
        self.responsive_manager.remove_resize_callback(self._on_resize)
        super().destroy()


def setup_responsive_window(root, min_width=800, min_height=600, 
                           default_width=1000, default_height=700):
    """
    设置响应式窗口
    
    Args:
        root: Tk根窗口
        min_width: 最小宽度
        min_height: 最小高度
        default_width: 默认宽度
        default_height: 默认高度
    """
    # 设置窗口标题和默认大小
    root.title("Minecraft 服务器控制面板 V0.1.5-beta3")
    root.geometry(f"{default_width}x{default_height}")
    
    # 设置窗口最小大小
    root.minsize(min_width, min_height)
    
    # 创建响应式管理器
    responsive_manager = ResponsiveManager(root)
    
    # 配置主窗口的grid权重，使其可以自适应
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    return responsive_manager


def create_responsive_container(parent, responsive_manager, padding="10"):
    """
    创建响应式容器Frame
    
    Args:
        parent: 父容器
        responsive_manager: 响应式管理器
        padding: 内边距
        
    Returns:
        ResponsiveFrame实例
    """
    container = ResponsiveFrame(parent, responsive_manager, padding=padding)
    container.pack(fill=tk.BOTH, expand=True)
    return container


# 响应式布局配置常量
RESPONSIVE_CONFIGS = {
    'button_widths': {
        'xs': 8,
        'sm': 10,
        'md': 12,
        'lg': 14,
        'xl': 16
    },
    'entry_widths': {
        'xs': 15,
        'sm': 20,
        'md': 25,
        'lg': 30,
        'xl': 35
    },
    'treeview_heights': {
        'xs': 6,
        'sm': 8,
        'md': 10,
        'lg': 12,
        'xl': 15
    },
    'text_heights': {
        'xs': 6,
        'sm': 8,
        'md': 10,
        'lg': 12,
        'xl': 15
    },
    'padding': {
        'xs': 5,
        'sm': 8,
        'md': 10,
        'lg': 12,
        'xl': 15
    },
    'font_sizes': {
        'xs': 8,
        'sm': 9,
        'md': 10,
        'lg': 11,
        'xl': 12
    }
}


def get_responsive_config(responsive_manager, config_type):
    """
    获取响应式配置值
    
    Args:
        responsive_manager: 响应式管理器
        config_type: 配置类型，如 'button_widths', 'entry_widths' 等
        
    Returns:
        当前屏幕尺寸对应的配置值
    """
    if config_type in RESPONSIVE_CONFIGS:
        return responsive_manager.get_responsive_value(RESPONSIVE_CONFIGS[config_type])
    return None
