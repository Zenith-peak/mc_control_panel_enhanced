import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import threading
import time
from collections import OrderedDict
import re

class PlayerFilter:
    """
    玩家筛选模块，提供高效的玩家筛选和自动补全功能
    """
    def __init__(self, control_panel):
        """
        初始化玩家筛选器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        
        self.all_players = []
        self.filtered_players = []
        
        self.player_cache = {}
        self.cache_timestamp = 0
        self.cache_ttl = 5
        
        self.filter_debounce_timer = None
        self.debounce_delay = 150
        
        self.autocomplete_index = -1
        self.autocomplete_matches = []
        
        self.filter_criteria = {
            'name': '',
            'status': 'all',
            'gamemode': 'all',
            'ping_min': 0,
            'ping_max': 500,
            'online_time_min': 0,
            'online_time_max': 9999,
            'level_min': 0,
            'level_max': 100,
            'last_login_days': 365
        }
        
        self.player_data = {}
        
    def update_player_data(self, player_name, data):
        """
        更新玩家数据
        
        Args:
            player_name: 玩家名称
            data: 玩家数据字典
        """
        if player_name not in self.player_data:
            self.player_data[player_name] = {
                'name': player_name,
                'status': '离线',
                'gamemode': '未知',
                'ping': 0,
                'online_time': 0,
                'level': 0,
                'last_login': None,
                'position': (0, 64, 0),
                'join_count': 0
            }
        
        self.player_data[player_name].update(data)
        self._invalidate_cache()
    
    def remove_player_data(self, player_name):
        """
        移除玩家数据
        
        Args:
            player_name: 玩家名称
        """
        if player_name in self.player_data:
            del self.player_data[player_name]
            self._invalidate_cache()
    
    def get_player_data(self, player_name):
        """
        获取玩家数据
        
        Args:
            player_name: 玩家名称
            
        Returns:
            dict: 玩家数据
        """
        return self.player_data.get(player_name, {})
    
    def _invalidate_cache(self):
        """使缓存失效"""
        self.cache_timestamp = 0
    
    def set_filter_criteria(self, **kwargs):
        """
        设置筛选条件
        
        Args:
            **kwargs: 筛选条件键值对
        """
        for key, value in kwargs.items():
            if key in self.filter_criteria:
                self.filter_criteria[key] = value
        self._invalidate_cache()
    
    def reset_filter_criteria(self):
        """重置筛选条件"""
        self.filter_criteria = {
            'name': '',
            'status': 'all',
            'gamemode': 'all',
            'ping_min': 0,
            'ping_max': 500,
            'online_time_min': 0,
            'online_time_max': 9999,
            'level_min': 0,
            'level_max': 100,
            'last_login_days': 365
        }
        self._invalidate_cache()
    
    def filter_players(self, players=None):
        """
        根据筛选条件过滤玩家列表
        
        Args:
            players: 要过滤的玩家列表，如果为None则使用所有玩家
            
        Returns:
            list: 过滤后的玩家列表
        """
        if players is None:
            players = list(self.player_data.values())
        
        if not self.filter_criteria['name'] and \
           self.filter_criteria['status'] == 'all' and \
           self.filter_criteria['gamemode'] == 'all' and \
           self.filter_criteria['ping_min'] == 0 and \
           self.filter_criteria['ping_max'] == 500:
            return players
        
        filtered = []
        criteria = self.filter_criteria
        
        for player in players:
            if not self._match_filter(player, criteria):
                continue
            filtered.append(player)
        
        self.filtered_players = filtered
        return filtered
    
    def _match_filter(self, player, criteria):
        """
        检查玩家是否匹配筛选条件
        
        Args:
            player: 玩家数据字典
            criteria: 筛选条件字典
            
        Returns:
            bool: 是否匹配
        """
        if criteria['name']:
            name_lower = criteria['name'].lower()
            player_name = player.get('name', '').lower()
            if name_lower not in player_name:
                if not self._fuzzy_match(player_name, name_lower):
                    return False
        
        if criteria['status'] != 'all':
            if player.get('status', '') != criteria['status']:
                return False
        
        if criteria['gamemode'] != 'all':
            if player.get('gamemode', '') != criteria['gamemode']:
                return False
        
        ping = player.get('ping', 0)
        if ping < criteria['ping_min'] or ping > criteria['ping_max']:
            return False
        
        online_time = player.get('online_time', 0)
        if online_time < criteria['online_time_min'] or online_time > criteria['online_time_max']:
            return False
        
        level = player.get('level', 0)
        if level < criteria['level_min'] or level > criteria['level_max']:
            return False
        
        last_login = player.get('last_login')
        if last_login and criteria['last_login_days'] < 365:
            if isinstance(last_login, str):
                try:
                    last_login = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')
                except:
                    last_login = None
            
            if last_login:
                days_since_login = (datetime.now() - last_login).days
                if days_since_login > criteria['last_login_days']:
                    return False
        
        return True
    
    def _fuzzy_match(self, text, pattern):
        """
        模糊匹配
        
        Args:
            text: 目标文本
            pattern: 匹配模式
            
        Returns:
            bool: 是否匹配
        """
        if not pattern:
            return True
        
        text_lower = text.lower()
        pattern_lower = pattern.lower()
        
        pattern_idx = 0
        for char in text_lower:
            if pattern_idx < len(pattern_lower) and char == pattern_lower[pattern_idx]:
                pattern_idx += 1
        
        return pattern_idx == len(pattern_lower)
    
    def get_autocomplete_suggestions(self, partial_name, max_suggestions=10):
        """
        获取自动补全建议
        
        Args:
            partial_name: 部分玩家名称
            max_suggestions: 最大建议数量
            
        Returns:
            list: 建议的玩家名称列表
        """
        if not partial_name:
            online_players = []
            if hasattr(self.control_panel, 'player_manager'):
                online_players = self.control_panel.player_manager.players_online
            
            suggestions = list(online_players)
            
            all_player_names = list(self.player_data.keys())
            for name in all_player_names:
                if name not in suggestions:
                    suggestions.append(name)
            
            return suggestions[:max_suggestions]
        
        partial_lower = partial_name.lower()
        exact_matches = []
        prefix_matches = []
        contains_matches = []
        fuzzy_matches = []
        
        online_players = []
        if hasattr(self.control_panel, 'player_manager'):
            online_players = self.control_panel.player_manager.players_online
        
        for player in online_players:
            player_lower = player.lower()
            score = self._calculate_match_score(player_lower, partial_lower)
            
            if score == 100:
                exact_matches.append((player, score))
            elif player_lower.startswith(partial_lower):
                prefix_matches.append((player, score))
            elif partial_lower in player_lower:
                contains_matches.append((player, score))
            else:
                fuzzy_score = self._fuzzy_match_score(player_lower, partial_lower)
                if fuzzy_score > 0:
                    fuzzy_matches.append((player, fuzzy_score))
        
        for player in self.player_data.keys():
            if player in online_players:
                continue
            
            player_lower = player.lower()
            score = self._calculate_match_score(player_lower, partial_lower)
            
            if score == 100:
                exact_matches.append((player, score))
            elif player_lower.startswith(partial_lower):
                prefix_matches.append((player, score))
            elif partial_lower in player_lower:
                contains_matches.append((player, score))
            else:
                fuzzy_score = self._fuzzy_match_score(player_lower, partial_lower)
                if fuzzy_score > 0:
                    fuzzy_matches.append((player, fuzzy_score))
        
        all_matches = exact_matches + prefix_matches + contains_matches + fuzzy_matches
        all_matches.sort(key=lambda x: (-x[1], x[0]))
        
        return [match[0] for match in all_matches[:max_suggestions]]
    
    def _calculate_match_score(self, player_name, partial):
        """
        计算匹配得分
        
        Args:
            player_name: 玩家名称（小写）
            partial: 部分名称（小写）
            
        Returns:
            int: 匹配得分（0-100）
        """
        if player_name == partial:
            return 100
        
        if player_name.startswith(partial):
            return 90
        
        if partial in player_name:
            return 70
        
        return 0
    
    def _fuzzy_match_score(self, text, pattern):
        """
        计算模糊匹配得分
        
        Args:
            text: 目标文本
            pattern: 匹配模式
            
        Returns:
            int: 匹配得分（0-60）
        """
        if not pattern:
            return 0
        
        pattern_idx = 0
        consecutive_bonus = 0
        last_match_idx = -2
        
        for i, char in enumerate(text):
            if pattern_idx < len(pattern) and char == pattern[pattern_idx]:
                if i == last_match_idx + 1:
                    consecutive_bonus += 5
                
                last_match_idx = i
                pattern_idx += 1
        
        if pattern_idx == len(pattern):
            base_score = 40
            length_penalty = len(text) - len(pattern)
            return max(10, base_score - length_penalty + consecutive_bonus)
        
        return 0
    
    def get_next_autocomplete(self, partial_name):
        """
        获取下一个自动补全结果
        
        Args:
            partial_name: 部分玩家名称
            
        Returns:
            tuple: (补全后的名称, 是否有更多建议)
        """
        if not self.autocomplete_matches or self.autocomplete_index == -1:
            self.autocomplete_matches = self.get_autocomplete_suggestions(partial_name)
            self.autocomplete_index = 0
        
        if not self.autocomplete_matches:
            return (partial_name, False)
        
        if self.autocomplete_index >= len(self.autocomplete_matches):
            self.autocomplete_index = 0
        
        result = self.autocomplete_matches[self.autocomplete_index]
        self.autocomplete_index += 1
        
        has_more = self.autocomplete_index < len(self.autocomplete_matches)
        return (result, has_more)
    
    def reset_autocomplete(self):
        """重置自动补全状态"""
        self.autocomplete_index = -1
        self.autocomplete_matches = []
    
    def filter_with_debounce(self, callback, **kwargs):
        """
        带防抖的筛选
        
        Args:
            callback: 筛选完成后的回调函数
            **kwargs: 筛选条件
        """
        if self.filter_debounce_timer:
            self.control_panel.root.after_cancel(self.filter_debounce_timer)
        
        def do_filter():
            self.set_filter_criteria(**kwargs)
            result = self.filter_players()
            if callback:
                callback(result)
        
        self.filter_debounce_timer = self.control_panel.root.after(
            self.debounce_delay, 
            do_filter
        )
    
    def quick_search(self, keyword):
        """
        快速搜索玩家
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            list: 匹配的玩家列表
        """
        if not keyword:
            return list(self.player_data.values())
        
        results = []
        keyword_lower = keyword.lower()
        
        for player_name, player_info in self.player_data.items():
            if keyword_lower in player_name.lower():
                results.append(player_info)
        
        return results
    
    def get_player_statistics(self):
        """
        获取玩家统计信息
        
        Returns:
            dict: 统计信息
        """
        total_players = len(self.player_data)
        online_players = 0
        active_players = 0
        
        for player_info in self.player_data.values():
            if player_info.get('status') == '活跃':
                online_players += 1
            
            last_login = player_info.get('last_login')
            if last_login:
                if isinstance(last_login, str):
                    try:
                        last_login = datetime.strptime(last_login, '%Y-%m-%d %H:%M:%S')
                    except:
                        continue
                
                if last_login and (datetime.now() - last_login).days <= 7:
                    active_players += 1
        
        return {
            'total': total_players,
            'online': online_players,
            'active': active_players,
            'offline': total_players - online_players
        }


class PlayerFilterUI:
    """
    玩家筛选UI组件
    """
    def __init__(self, parent, control_panel, filter_manager, on_filter_callback=None):
        """
        初始化筛选UI
        
        Args:
            parent: 父容器
            control_panel: 主控制面板实例
            filter_manager: PlayerFilter实例
            on_filter_callback: 筛选回调函数
        """
        self.parent = parent
        self.control_panel = control_panel
        self.filter_manager = filter_manager
        self.on_filter_callback = on_filter_callback
        
        self.filter_vars = {}
        self.create_filter_ui()
    
    def create_filter_ui(self):
        """创建筛选UI"""
        self.filter_frame = ttk.LabelFrame(self.parent, text="玩家筛选", padding="8")
        self.filter_frame.pack(fill=tk.X, pady=(0, 8))
        
        search_frame = ttk.Frame(self.filter_frame)
        search_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_vars['name'] = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.filter_vars['name'], width=25)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)
        self.search_entry.bind('<Tab>', self._on_autocomplete)
        self.search_entry.bind('<Return>', self._on_apply_filter)
        
        self.autocomplete_hint_var = tk.StringVar(value="")
        self.autocomplete_hint = ttk.Label(search_frame, textvariable=self.autocomplete_hint_var, 
                                           foreground="gray", font=('微软雅黑', 9))
        self.autocomplete_hint.pack(side=tk.LEFT, padx=(0, 8))
        
        self.filter_button = ttk.Button(search_frame, text="筛选", command=self._on_apply_filter, width=8)
        self.filter_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.reset_button = ttk.Button(search_frame, text="重置", command=self._on_reset_filter, width=8)
        self.reset_button.pack(side=tk.LEFT)
        
        advanced_frame = ttk.Frame(self.filter_frame)
        advanced_frame.pack(fill=tk.X)
        
        ttk.Label(advanced_frame, text="状态:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['status'] = tk.StringVar(value="all")
        status_combo = ttk.Combobox(advanced_frame, textvariable=self.filter_vars['status'],
                                    values=["all", "活跃", "离线", "延迟"], width=8, state="readonly")
        status_combo.pack(side=tk.LEFT, padx=(0, 12))
        status_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        ttk.Label(advanced_frame, text="游戏模式:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['gamemode'] = tk.StringVar(value="all")
        gamemode_combo = ttk.Combobox(advanced_frame, textvariable=self.filter_vars['gamemode'],
                                      values=["all", "生存", "创造", "冒险", "旁观"], width=8, state="readonly")
        gamemode_combo.pack(side=tk.LEFT, padx=(0, 12))
        gamemode_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        ttk.Label(advanced_frame, text="延迟:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['ping_min'] = tk.StringVar(value="0")
        ping_min_entry = ttk.Entry(advanced_frame, textvariable=self.filter_vars['ping_min'], width=5)
        ping_min_entry.pack(side=tk.LEFT)
        ttk.Label(advanced_frame, text="-").pack(side=tk.LEFT, padx=(2, 2))
        self.filter_vars['ping_max'] = tk.StringVar(value="500")
        ping_max_entry = ttk.Entry(advanced_frame, textvariable=self.filter_vars['ping_max'], width=5)
        ping_max_entry.pack(side=tk.LEFT, padx=(0, 12))
        
        ttk.Label(advanced_frame, text="等级:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['level_min'] = tk.StringVar(value="0")
        level_min_entry = ttk.Entry(advanced_frame, textvariable=self.filter_vars['level_min'], width=5)
        level_min_entry.pack(side=tk.LEFT)
        ttk.Label(advanced_frame, text="-").pack(side=tk.LEFT, padx=(2, 2))
        self.filter_vars['level_max'] = tk.StringVar(value="100")
        level_max_entry = ttk.Entry(advanced_frame, textvariable=self.filter_vars['level_max'], width=5)
        level_max_entry.pack(side=tk.LEFT)
        
        self.advanced_frame = ttk.Frame(self.filter_frame)
        
        ttk.Label(self.advanced_frame, text="最近登录:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['last_login_days'] = tk.StringVar(value="365")
        last_login_combo = ttk.Combobox(self.advanced_frame, textvariable=self.filter_vars['last_login_days'],
                                        values=["1", "7", "30", "90", "180", "365"], width=6, state="readonly")
        last_login_combo.pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(self.advanced_frame, text="天内").pack(side=tk.LEFT, padx=(0, 12))
        last_login_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        ttk.Label(self.advanced_frame, text="在线时间:").pack(side=tk.LEFT, padx=(0, 5))
        self.filter_vars['online_time_min'] = tk.StringVar(value="0")
        online_min_entry = ttk.Entry(self.advanced_frame, textvariable=self.filter_vars['online_time_min'], width=5)
        online_min_entry.pack(side=tk.LEFT)
        ttk.Label(self.advanced_frame, text="-").pack(side=tk.LEFT, padx=(2, 2))
        self.filter_vars['online_time_max'] = tk.StringVar(value="9999")
        online_max_entry = ttk.Entry(self.advanced_frame, textvariable=self.filter_vars['online_time_max'], width=5)
        online_max_entry.pack(side=tk.LEFT)
        ttk.Label(self.advanced_frame, text="分钟").pack(side=tk.LEFT)
        
        self.advanced_frame.pack(fill=tk.X, pady=(8, 0))
        self.advanced_frame.pack_forget()
        
        self.show_advanced_var = tk.BooleanVar(value=False)
        self.advanced_toggle = ttk.Checkbutton(self.filter_frame, text="显示高级筛选",
                                               variable=self.show_advanced_var,
                                               command=self._toggle_advanced)
        self.advanced_toggle.pack(anchor=tk.W, pady=(8, 0))
    
    def _toggle_advanced(self):
        """切换高级筛选显示"""
        if self.show_advanced_var.get():
            self.advanced_frame.pack(fill=tk.X, pady=(8, 0))
        else:
            self.advanced_frame.pack_forget()
    
    def _on_search_change(self, event):
        """搜索内容变化事件"""
        search_text = self.filter_vars['name'].get()
        
        if len(search_text) >= 1:
            suggestions = self.filter_manager.get_autocomplete_suggestions(search_text, max_suggestions=5)
            if suggestions:
                self.autocomplete_hint_var.set(f"按Tab补全: {suggestions[0]}")
            else:
                self.autocomplete_hint_var.set("无匹配结果")
        else:
            self.autocomplete_hint_var.set("")
            self.filter_manager.reset_autocomplete()
        
        self.filter_manager.filter_with_debounce(
            self._on_filter_complete,
            name=search_text
        )
    
    def _on_autocomplete(self, event):
        """Tab键自动补全"""
        search_text = self.filter_vars['name'].get()
        completed, has_more = self.filter_manager.get_next_autocomplete(search_text)
        
        self.filter_vars['name'].set(completed)
        self.search_entry.select_range(0, tk.END)
        self.search_entry.icursor(tk.END)
        
        if has_more:
            self.autocomplete_hint_var.set("继续按Tab查看更多")
        else:
            self.autocomplete_hint_var.set("已是最后一个")
        
        return "break"
    
    def _on_filter_change(self, event):
        """筛选条件变化事件"""
        self._apply_filter()
    
    def _on_apply_filter(self, event=None):
        """应用筛选按钮点击事件"""
        self._apply_filter()
    
    def _on_reset_filter(self):
        """重置筛选条件"""
        self.filter_vars['name'].set('')
        self.filter_vars['status'].set('all')
        self.filter_vars['gamemode'].set('all')
        self.filter_vars['ping_min'].set('0')
        self.filter_vars['ping_max'].set('500')
        self.filter_vars['level_min'].set('0')
        self.filter_vars['level_max'].set('100')
        self.filter_vars['last_login_days'].set('365')
        self.filter_vars['online_time_min'].set('0')
        self.filter_vars['online_time_max'].set('9999')
        
        self.autocomplete_hint_var.set("")
        self.filter_manager.reset_autocomplete()
        self.filter_manager.reset_filter_criteria()
        
        if self.on_filter_callback:
            self.on_filter_callback(list(self.filter_manager.player_data.values()))
    
    def _apply_filter(self):
        """应用筛选条件"""
        try:
            criteria = {
                'name': self.filter_vars['name'].get(),
                'status': self.filter_vars['status'].get(),
                'gamemode': self.filter_vars['gamemode'].get(),
                'ping_min': int(self.filter_vars['ping_min'].get() or 0),
                'ping_max': int(self.filter_vars['ping_max'].get() or 500),
                'level_min': int(self.filter_vars['level_min'].get() or 0),
                'level_max': int(self.filter_vars['level_max'].get() or 100),
                'last_login_days': int(self.filter_vars['last_login_days'].get() or 365),
                'online_time_min': int(self.filter_vars['online_time_min'].get() or 0),
                'online_time_max': int(self.filter_vars['online_time_max'].get() or 9999)
            }
            
            self.filter_manager.filter_with_debounce(
                self._on_filter_complete,
                **criteria
            )
        except ValueError:
            pass
    
    def _on_filter_complete(self, filtered_players):
        """筛选完成回调"""
        if self.on_filter_callback:
            self.on_filter_callback(filtered_players)
    
    def get_filter_frame(self):
        """获取筛选框架"""
        return self.filter_frame
