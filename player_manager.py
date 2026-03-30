import tkinter as tk
import re
from datetime import datetime

class PlayerManager:
    """
    玩家管理模块，负责玩家相关的操作和数据管理
    """
    def __init__(self, control_panel):
        """
        初始化玩家管理器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.players_online = []
        
    def update_players_display(self):
        """
        更新在线玩家显示
        """
        max_players = self.control_panel.property_vars.get("max-players", tk.StringVar(value="20")).get()
        try:
            max_players_int = int(max_players)
        except:
            max_players_int = 20
            
        self.control_panel.players_var.set(f"在线玩家: {len(self.players_online)}/{max_players_int}")
        
        if len(self.players_online) == 0:
            activity = "无"
        elif len(self.players_online) < 3:
            activity = "低"
        elif len(self.players_online) < 10:
            activity = "中"
        else:
            activity = "高"
        self.control_panel.player_activity_var.set(f"活跃度: {activity}")
        
        for item in self.control_panel.players_tree.get_children():
            self.control_panel.players_tree.delete(item)
            
        for player in self.players_online:
            pos = self.control_panel.message_manager.get_player_position(player)
            ping = self.control_panel.message_manager.get_player_ping(player)
            position_str = f"{pos[0]:.0f}, {pos[1]:.0f}, {pos[2]:.0f}"
            
            status = "活跃" if ping < 100 else "延迟"
            
            online_time = "00:05:30"
            
            gamemode = "生存"
            
            self.control_panel.players_tree.insert("", tk.END, values=(status, player, position_str, f"{ping}ms", gamemode, online_time))
            
            if hasattr(self.control_panel, 'player_filter'):
                self.control_panel.player_filter.update_player_data(player, {
                    'name': player,
                    'status': status,
                    'position': pos,
                    'ping': ping,
                    'gamemode': gamemode,
                    'online_time': 5,
                    'last_login': datetime.now()
                })
    
    def parse_player_join(self, output):
        """
        解析玩家加入消息
        
        Args:
            output: 服务器输出消息
        """
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
                        self.control_panel.message_manager.update_player_position(player, 0, 64, 0)
                        self.control_panel.message_manager.update_player_ping(player, 50)
                        self.update_players_display()
                        # 添加加入消息
                        self.control_panel.message_manager.add_message(player, f"{player} 加入了游戏", is_server=True)
                    break
        except Exception as e:
            self.control_panel.log_message(f"错误: 解析玩家加入消息时出错: {str(e)}")
    
    def parse_player_leave(self, output):
        """
        解析玩家离开消息
        
        Args:
            output: 服务器输出消息
        """
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
                        self.control_panel.message_manager.add_message(player, f"{player} 离开了游戏", is_server=True)
                    break
        except Exception as e:
            self.control_panel.log_message(f"错误: 解析玩家离开消息时出错: {str(e)}")
    
    def parse_player_list(self, output):
        """
        解析玩家列表命令的输出
        
        Args:
            output: 服务器输出消息
        """
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
                self.control_panel.players_var.set(f"在线玩家: {online_count}/{max_players}")
        except Exception as e:
            self.control_panel.log_message(f"错误: 解析玩家列表时出错: {str(e)}")
    
    def get_selected_player(self):
        """
        获取选中的玩家
        
        Returns:
            str: 选中的玩家名称，或None
        """
        selection = self.control_panel.players_tree.selection()
        if selection:
            values = self.control_panel.players_tree.item(selection[0])['values']
            # 新格式中玩家名称在第二列
            if len(values) >= 6:
                return values[1]
            else:
                # 兼容旧格式
                return values[0]
        return None
    
    def kick_player(self, player, reason=""):
        """
        踢出玩家
        
        Args:
            player: 玩家名称
            reason: 踢出原因
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
            
        if reason:
            return self.control_panel.send_server_command(f"kick {player} {reason}")
        else:
            return self.control_panel.send_server_command(f"kick {player}")
    
    def teleport_player(self, player, destination):
        """
        传送玩家
        
        Args:
            player: 玩家名称
            destination: 目标位置
            
        Returns:
            bool: 操作是否成功
        """
        if not player or not destination:
            return False
            
        return self.control_panel.send_server_command(f"tp {player} {destination}")
    
    def op_player(self, player):
        """
        设为管理员
        
        Args:
            player: 玩家名称
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
            
        return self.control_panel.send_server_command(f"op {player}")
    
    def deop_player(self, player):
        """
        取消管理员
        
        Args:
            player: 玩家名称
            
        Returns:
            bool: 操作是否成功
        """
        if not player:
            return False
            
        return self.control_panel.send_server_command(f"deop {player}")
    
    def refresh_player_list(self):
        """
        刷新玩家列表
        
        Returns:
            bool: 操作是否成功
        """
        if self.control_panel.server_manager.server_running:
            return self.control_panel.send_server_command("list")
        else:
            self.control_panel.log_message("警告: 服务器未运行，无法刷新玩家列表")
            return False
