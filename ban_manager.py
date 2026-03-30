import threading
import time
from datetime import datetime, timedelta

class BanManager:
    """
    封禁管理模块，负责玩家封禁和禁言相关的功能
    """
    def __init__(self, control_panel):
        """
        初始化封禁管理器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.temp_bans = {}
        self.muted_players = {}
        self.ban_monitor_thread = None
        self.ban_monitoring = False
        self.mute_monitor_thread = None
        self.mute_monitoring = False
    
    def start_ban_monitoring(self):
        """
        启动封禁监控
        """
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
                    self.control_panel.send_server_command(f"pardon {player}")
                    del self.temp_bans[player]
                    
                    # 从封禁列表中移除
                    self.control_panel.banned_players = [b for b in self.control_panel.banned_players if b["player"] != player]
                    
                    # 更新显示
                    self.control_panel.root.after(0, self.control_panel.load_banned_players)
                    self.control_panel.root.after(0, lambda: self.control_panel.log_message(f"自动解封玩家: {player}"))
                
                time.sleep(60)  # 每分钟检查一次
        
        self.ban_monitor_thread = threading.Thread(target=monitor_bans)
        self.ban_monitor_thread.daemon = True
        self.ban_monitor_thread.start()
    
    def start_mute_monitoring(self):
        """
        启动禁言监控
        """
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
                    self.control_panel.send_server_command(f"unmute {player}")
                    del self.muted_players[player]
                    
                    # 更新显示
                    self.control_panel.root.after(0, self.control_panel.load_muted_players)
                    self.control_panel.root.after(0, lambda: self.control_panel.log_message(f"自动解除玩家禁言: {player}"))
                
                time.sleep(60)  # 每分钟检查一次
        
        self.mute_monitor_thread = threading.Thread(target=monitor_mutes)
        self.mute_monitor_thread.daemon = True
        self.mute_monitor_thread.start()
    
    def ban_player(self, player, reason, ban_type, ban_time=None):
        """
        封禁玩家
        
        Args:
            player: 玩家名称
            reason: 封禁原因
            ban_type: 封禁类型 ("永久" 或 "临时")
            ban_time: 临时封禁时间 (如 "1h", "2d" 等)
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
        
        if ban_type == "永久":
            # 永久封禁
            if reason:
                result = self.control_panel.send_server_command(f"ban {player} {reason}")
            else:
                result = self.control_panel.send_server_command(f"ban {player}")
            
            if result:
                # 添加到封禁列表
                ban_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.control_panel.banned_players.append({
                    "player": player,
                    "reason": reason,
                    "ban_date": ban_date,
                    "unban_date": "永久",
                    "ban_type": "永久"
                })
                return True
        else:
            # 临时封禁
            if reason:
                result = self.control_panel.send_server_command(f"ban {player} {reason}")
            else:
                result = self.control_panel.send_server_command(f"ban {player}")
            
            if result:
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
                
                self.control_panel.banned_players.append({
                    "player": player,
                    "reason": reason,
                    "ban_date": ban_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "unban_date": unban_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "ban_type": "临时"
                })
                return True
        
        return False
    
    def pardon_player(self, player):
        """
        解除封禁玩家
        
        Args:
            player: 玩家名称
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
        
        # 发送解封命令
        result = self.control_panel.send_server_command(f"pardon {player}")
        
        if result:
            # 从列表中移除
            if player in self.temp_bans:
                del self.temp_bans[player]
            
            # 从封禁列表中移除
            self.control_panel.banned_players = [b for b in self.control_panel.banned_players if b["player"] != player]
            return True
        
        return False
    
    def mute_player(self, player, reason, mute_type, mute_time=None):
        """
        禁言玩家
        
        Args:
            player: 玩家名称
            reason: 禁言原因
            mute_type: 禁言类型 ("永久" 或 "临时")
            mute_time: 临时禁言时间 (如 "1h", "2d" 等)
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
        
        if mute_type == "永久":
            # 永久禁言
            if reason:
                result = self.control_panel.send_server_command(f"mute {player} {reason}")
            else:
                result = self.control_panel.send_server_command(f"mute {player}")
            
            if result:
                # 添加到禁言列表
                mute_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.muted_players[player] = {
                    "type": "permanent",
                    "reason": reason,
                    "mute_date": mute_date,
                    "unmute_date": "永久"
                }
                return True
        else:
            # 临时禁言
            if reason:
                result = self.control_panel.send_server_command(f"mute {player} {mute_time} {reason}")
            else:
                result = self.control_panel.send_server_command(f"mute {player} {mute_time}")
            
            if result:
                # 计算解禁时间
                mute_date = datetime.now()
                unmute_date = self.calculate_unban_date(mute_date, mute_time)
                
                # 添加到临时禁言列表
                self.muted_players[player] = {
                    "type": "temporary",
                    "mute_date": mute_date,
                    "unmute_date": unmute_date,
                    "reason": reason,
                    "mute_time": mute_time
                }
                return True
        
        return False
    
    def unmute_player(self, player):
        """
        解除禁言玩家
        
        Args:
            player: 玩家名称
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
        
        # 发送解禁命令
        result = self.control_panel.send_server_command(f"unmute {player}")
        
        if result:
            # 从列表中移除
            if player in self.muted_players:
                del self.muted_players[player]
            return True
        
        return False
    
    def calculate_unban_date(self, ban_date, ban_time):
        """
        计算解封时间
        
        Args:
            ban_date: 封禁开始时间
            ban_time: 封禁时长 (如 "1h", "2d" 等)
            
        Returns:
            datetime: 解封时间
        """
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
    
    def update_ban_times(self):
        """
        更新封禁剩余时间显示
        """
        current_time = datetime.now()
        
        for item in self.control_panel.ban_tree.get_children():
            values = self.control_panel.ban_tree.item(item)['values']
            player = values[0]  # 第一列是玩家名称
            
            if player in self.temp_bans:
                ban_info = self.temp_bans[player]
                time_left = ban_info["unban_date"] - current_time
                
                if time_left.total_seconds() <= 0:
                    # 时间已到，自动解封
                    self.control_panel.send_server_command(f"pardon {player}")
                    del self.temp_bans[player]
                    self.control_panel.banned_players = [b for b in self.control_panel.banned_players if b["player"] != player]
                else:
                    # 更新剩余时间显示
                    hours, remainder = divmod(int(time_left.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m"
                    else:
                        time_str = f"{minutes}m {seconds}s"
                    
                    # 更新显示
                    self.control_panel.ban_tree.set(item, "剩余时间", time_str)
        
        # 重新加载封禁列表以确保显示最新数据
        self.control_panel.load_banned_players()
    
    def update_mute_times(self):
        """
        更新禁言剩余时间显示
        """
        current_time = datetime.now()
        
        for item in self.control_panel.mute_tree.get_children():
            values = self.control_panel.mute_tree.item(item)['values']
            player = values[0]  # 第一列是玩家名称
            
            if player in self.muted_players:
                mute_info = self.muted_players[player]
                if mute_info.get("type") == "temporary" and isinstance(mute_info.get("unmute_date"), datetime):
                    time_left = mute_info["unmute_date"] - current_time
                    
                    if time_left.total_seconds() <= 0:
                        # 时间已到，自动解禁
                        self.control_panel.send_server_command(f"unmute {player}")
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
                        self.control_panel.mute_tree.set(item, "剩余时间", time_str)
        
        # 重新加载禁言列表以确保显示最新数据
        self.control_panel.load_muted_players()
