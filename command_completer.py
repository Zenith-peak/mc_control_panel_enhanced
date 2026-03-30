import json
import os

class CommandCompleter:
    """
    命令自动补全模块，负责Minecraft命令的自动补全和提示
    """
    def __init__(self, control_panel):
        """
        初始化命令补全器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.commands = {}
        self.load_commands()
    
    def load_commands(self):
        """
        加载Minecraft命令数据
        """
        try:
            # 尝试从外部文件加载
            if os.path.exists("mc_commands.json"):
                with open("mc_commands.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.commands = data.get('commands', {})
            else:
                # 内置基本命令数据
                self.commands = {
                    "help": {"description": "显示命令帮助", "usage": "/help [页码|命令名]", "permission": 0},
                    "list": {"description": "列出服务器上的玩家", "usage": "/list", "permission": 0},
                    "gamemode": {"description": "更改游戏模式", "usage": "/gamemode <模式> [玩家]", "permission": 2, "suggestions": ["survival", "creative", "adventure", "spectator"]},
                    "give": {"description": "给予玩家物品", "usage": "/give <玩家> <物品> [数量] [数据值] [组件]", "permission": 2},
                    "tp": {"description": "传送实体", "usage": "/tp <目标玩家> <目的地玩家> 或 /tp <玩家> <x> <y> <z>", "permission": 2},
                    "teleport": {"description": "传送实体", "usage": "/teleport <目标玩家> <目的地玩家> 或 /teleport <玩家> <x> <y> <z>", "permission": 2},
                    "time": {"description": "更改或查询世界游戏时间", "usage": "/time <set|add|query> <值>", "permission": 2, "suggestions": ["set", "add", "query"]},
                    "weather": {"description": "设置天气", "usage": "/weather <clear|rain|thunder> [持续时间]", "permission": 2, "suggestions": ["clear", "rain", "thunder"]},
                    "op": {"description": "授予玩家管理员权限", "usage": "/op <玩家>", "permission": 3},
                    "deop": {"description": "撤销玩家的管理员权限", "usage": "/deop <玩家>", "permission": 3},
                    "ban": {"description": "封禁玩家", "usage": "/ban <玩家> [原因]", "permission": 3},
                    "tempban": {"description": "临时封禁玩家", "usage": "/tempban <玩家> <时间> [原因]", "permission": 3},
                    "pardon": {"description": "解除封禁玩家", "usage": "/pardon <玩家>", "permission": 3},
                    "kick": {"description": "将玩家踢出服务器", "usage": "/kick <玩家> [原因]", "permission": 3},
                    "stop": {"description": "停止服务器", "usage": "/stop", "permission": 4},
                    "save-all": {"description": "保存服务器世界", "usage": "/save-all", "permission": 4},
                    "whitelist": {"description": "管理白名单", "usage": "/whitelist <on|off|list|add|remove|reload>", "permission": 3, "suggestions": ["on", "off", "list", "add", "remove", "reload"]},
                    "say": {"description": "向所有玩家发送消息", "usage": "/say <消息>", "permission": 1},
                    "tell": {"description": "向其他玩家发送私信", "usage": "/tell <玩家> <消息>", "permission": 0},
                    "msg": {"description": "向其他玩家发送私信", "usage": "/msg <玩家> <消息>", "permission": 0},
                    "seed": {"description": "显示世界种子", "usage": "/seed", "permission": 0},
                    "effect": {"description": "管理状态效果", "usage": "/effect <玩家> <效果> [秒数] [强度] [隐藏粒子]", "permission": 2},
                    "spawnpoint": {"description": "设置玩家出生点", "usage": "/spawnpoint [玩家] [x] [y] [z]", "permission": 2},
                    "setworldspawn": {"description": "设置世界出生点", "usage": "/setworldspawn [x] [y] [z]", "permission": 2},
                    "gamerule": {"description": "更改或查询游戏规则", "usage": "/gamerule <规则> [值]", "permission": 2},
                    "clear": {"description": "清除玩家物品", "usage": "/clear [玩家] [物品] [数据值] [最大数量] [数据标签]", "permission": 2},
                    "xp": {"description": "给予玩家经验", "usage": "/xp <数量> [玩家] 或 /xp <数量>L [玩家]", "permission": 2},
                    "defaultgamemode": {"description": "设置默认游戏模式", "usage": "/defaultgamemode <模式>", "permission": 2, "suggestions": ["survival", "creative", "adventure", "spectator"]},
                    "reload": {"description": "重载服务器数据", "usage": "/reload", "permission": 4},
                    "mute": {"description": "禁言玩家", "usage": "/mute <玩家> [时间] [原因]", "permission": 2},
                    "unmute": {"description": "解除玩家禁言", "usage": "/unmute <玩家>", "permission": 2}
                }
        except Exception as e:
            print(f"加载命令数据时出错: {e}")
    
    def get_command_suggestions(self, text):
        """
        获取命令建议
        
        Args:
            text: 输入的文本
            
        Returns:
            list: 命令建议列表
        """
        if not text.startswith('/'):
            return []
        
        text = text[1:]
        parts = text.split()
        
        if len(parts) == 0:
            return []
        
        command_name = parts[0]
        current_arg = parts[-1] if len(parts) > 1 else ""
        
        if len(parts) == 1:
            suggestions = []
            for cmd, info in self.commands.items():
                if cmd.startswith(command_name):
                    suggestions.append(f"/{cmd}")
            return suggestions
        
        if command_name in self.commands:
            cmd_info = self.commands[command_name]
            
            if "suggestions" in cmd_info:
                param_suggestions = []
                for suggestion in cmd_info["suggestions"]:
                    if suggestion.startswith(current_arg):
                        param_suggestions.append(suggestion)
                return param_suggestions
            
            if command_name in ["tp", "teleport", "kick", "ban", "tempban", "pardon", "op", "deop", "whitelist", "tell", "msg", "mute", "unmute"]:
                return self.get_online_players_suggestions(current_arg)
            elif command_name == "gamemode":
                return ["survival", "creative", "adventure", "spectator"]
            elif command_name == "time":
                if len(parts) == 2 and parts[1] in ["set", "add"]:
                    return ["day", "night", "noon", "midnight", "0", "1000", "6000", "12000", "18000"]
                elif len(parts) == 2:
                    return ["set", "add", "query"]
            elif command_name == "weather":
                return ["clear", "rain", "thunder"]
            elif command_name == "difficulty":
                return ["peaceful", "easy", "normal", "hard"]
            elif command_name == "tempban" or command_name == "mute":
                if len(parts) == 2:
                    return self.get_online_players_suggestions(current_arg)
                elif len(parts) == 3:
                    return ["1h", "2h", "6h", "12h", "1d", "7d", "30d", "1m", "6m", "1y"]
        
        return []
    
    def get_online_players_suggestions(self, current_arg):
        """
        获取在线玩家建议
        
        Args:
            current_arg: 当前输入的参数
            
        Returns:
            list: 在线玩家建议列表
        """
        if hasattr(self.control_panel, 'player_filter'):
            return self.control_panel.player_filter.get_autocomplete_suggestions(current_arg, max_suggestions=10)
        
        if hasattr(self.control_panel, 'player_manager'):
            online_players = self.control_panel.player_manager.players_online
        else:
            online_players = []
        
        if not online_players:
            sample_players = ["Steve", "Alex", "Notch", "Dinnerbone", "Herobrine"]
            return [player for player in sample_players if player.lower().startswith(current_arg.lower())]
        
        return [player for player in online_players if player.lower().startswith(current_arg.lower())]
    
    def get_command_info(self, command_name):
        """
        获取命令的详细信息
        
        Args:
            command_name: 命令名称
            
        Returns:
            dict: 命令信息字典
        """
        if command_name.startswith('/'):
            command_name = command_name[1:]
        
        if command_name in self.commands:
            return self.commands[command_name]
        return None
