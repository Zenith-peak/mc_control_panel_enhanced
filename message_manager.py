from datetime import datetime

class MessageManager:
    """
    消息管理模块，负责玩家消息、聊天记录和玩家数据的管理
    """
    def __init__(self, control_panel):
        """
        初始化消息管理器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.player_messages = {}  # 存储玩家消息 {player_name: [messages]}
        self.player_positions = {}  # 存储玩家位置 {player_name: (x, y, z)}
        self.player_ping = {}  # 存储玩家延迟 {player_name: ping}
        self.max_messages = 100  # 每个玩家的最大消息数量
    
    def add_message(self, player, message, is_server=False):
        """
        添加玩家消息
        
        Args:
            player: 玩家名称
            message: 消息内容
            is_server: 是否是服务器消息
        """
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
        if len(self.player_messages[player]) > self.max_messages:
            self.player_messages[player].pop(0)
        
        # 更新显示
        if hasattr(self.control_panel, 'update_player_chat_display'):
            self.control_panel.update_player_chat_display(player)
    
    def update_player_position(self, player, x, y, z):
        """
        更新玩家位置
        
        Args:
            player: 玩家名称
            x: X坐标
            y: Y坐标
            z: Z坐标
        """
        self.player_positions[player] = (x, y, z)
        if hasattr(self.control_panel, 'update_players_display'):
            self.control_panel.update_players_display()
    
    def update_player_ping(self, player, ping):
        """
        更新玩家延迟
        
        Args:
            player: 玩家名称
            ping: 延迟值（毫秒）
        """
        self.player_ping[player] = ping
        if hasattr(self.control_panel, 'update_players_display'):
            self.control_panel.update_players_display()
    
    def get_player_position(self, player):
        """
        获取玩家位置
        
        Args:
            player: 玩家名称
            
        Returns:
            tuple: 玩家坐标 (x, y, z)
        """
        return self.player_positions.get(player, (0, 0, 0))
    
    def get_player_ping(self, player):
        """
        获取玩家延迟
        
        Args:
            player: 玩家名称
            
        Returns:
            int: 延迟值（毫秒）
        """
        return self.player_ping.get(player, 0)
    
    def get_player_messages(self, player):
        """
        获取玩家消息
        
        Args:
            player: 玩家名称
            
        Returns:
            list: 消息列表
        """
        return self.player_messages.get(player, [])
    
    def clear_player_messages(self, player):
        """
        清空玩家消息
        
        Args:
            player: 玩家名称
        """
        if player in self.player_messages:
            del self.player_messages[player]
    
    def get_all_players(self):
        """
        获取所有有消息记录的玩家
        
        Returns:
            list: 玩家名称列表
        """
        return list(self.player_messages.keys())
