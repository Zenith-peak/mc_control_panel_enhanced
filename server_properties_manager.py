import os
import shutil
from datetime import datetime
from tkinter import messagebox


class ServerPropertiesManager:
    def __init__(self, panel):
        self.panel = panel
    
    def validate_port(self, value):
        if not value.isdigit() or not (1 <= int(value) <= 65535):
            return "端口号必须是1-65535之间的整数"
        return ""
    
    def validate_max_players(self, value):
        try:
            if not value or not value.strip():
                return "最大玩家数不能为空"
            if not value.strip().isdigit():
                return "最大玩家数必须是正整数"
            num = int(value.strip())
            if num < 1:
                return "最大玩家数必须大于0"
            if num > 1000:
                return "最大玩家数不能超过1000（建议值：1-100）"
            if num > 100:
                return "警告：超过100人可能影响服务器性能"
            return ""
        except ValueError:
            return "请输入有效的数字"
    
    def validate_view_distance(self, value):
        if not value.isdigit() or not (3 <= int(value) <= 32):
            return "视图距离必须是3-32之间的整数"
        return ""
    
    def validate_property(self, prop, var, validator):
        if validator:
            value = var.get()
            error = validator(value)
            self.panel.validation_vars[prop].set(error)
    
    def set_property_with_validation(self, prop, value):
        if prop in self.panel.validation_vars and self.panel.validation_vars[prop].get():
            messagebox.showerror("验证错误", self.panel.validation_vars[prop].get())
            return
        
        self.set_property(prop, value)
    
    def set_property(self, prop, value):
        self.panel.log_message(f"设置服务器属性: {prop}={value}")
        
        properties_file = os.path.join(self.panel.server_dir_var.get(), "server.properties")
        if os.path.exists(properties_file):
            try:
                properties = {}
                with open(properties_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key_value = line.split('=')
                            if len(key_value) == 2:
                                properties[key_value[0].strip()] = key_value[1].strip()
                
                properties[prop] = value
                
                with open(properties_file, 'w', encoding='utf-8') as f:
                    for key, val in properties.items():
                        f.write(f"{key}={val}\n")
                
                if prop == "server-port":
                    self.panel.server_port_var.set(value)
                    self.panel.update_server_address_display()
                
                if prop in ["max-players", "view-distance", "difficulty", "gamemode"]:
                    self.panel.send_server_command(f"{prop.replace('-', '')} {value}")
                
                messagebox.showinfo("成功", f"属性 {prop} 已设置为 {value}")
            except Exception as e:
                messagebox.showerror("错误", f"修改服务器属性时出错: {str(e)}")
        else:
            messagebox.showwarning("警告", "找不到 server.properties 文件")
    
    def apply_all_properties_with_validation(self):
        errors = []
        for prop, var in self.panel.property_vars.items():
            if prop in self.panel.validation_vars and self.panel.validation_vars[prop].get():
                errors.append(f"{prop}: {self.panel.validation_vars[prop].get()}")
        
        if errors:
            error_message = "验证失败:\n" + "\n".join(errors)
            messagebox.showerror("验证错误", error_message)
            return
        
        for prop, var in self.panel.property_vars.items():
            self.set_property(prop, var.get())
        messagebox.showinfo("成功", "所有服务器属性已应用")
    
    def load_server_properties(self):
        properties_file = os.path.join(self.panel.server_dir_var.get(), "server.properties")
        if os.path.exists(properties_file):
            try:
                self.backup_server_properties(properties_file)
                
                encodings = ['utf-8', 'gbk', 'latin-1']
                properties = {}
                success = False
                
                for encoding in encodings:
                    try:
                        properties = {}
                        with open(properties_file, 'r', encoding=encoding) as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith('#'):
                                    key_value = line.split('=')
                                    if len(key_value) == 2:
                                        properties[key_value[0].strip()] = key_value[1].strip()
                        success = True
                        break
                    except UnicodeDecodeError:
                        continue
                
                if not success:
                    self.panel.log_message("无法读取服务器属性文件，使用默认值")
                    return
                
                self.validate_server_properties(properties)
                
                for prop, var in self.panel.property_vars.items():
                    if prop in properties:
                        var.set(properties[prop])
                    else:
                        default_values = {
                            "server-port": "25565",
                            "online-mode": "true", 
                            "max-players": "20",
                            "view-distance": "10",
                            "white-list": "false",
                            "pvp": "true",
                            "difficulty": "easy",
                            "gamemode": "survival",
                            "spawn-monsters": "true",
                            "spawn-animals": "true",
                            "spawn-npcs": "true",
                            "allow-flight": "false",
                            "resource-pack": "",
                            "motd": "A Minecraft Server"
                        }
                        if prop in default_values:
                            var.set(default_values[prop])
                
                if 'server-port' in properties:
                    self.panel.server_port_var.set(properties['server-port'])
                    self.panel.update_server_address_display()
                
                if 'max-players' in properties:
                    self.panel.max_players_var.set(properties['max-players'])
                            
            except Exception as e:
                self.panel.log_message(f"加载服务器属性时出错: {str(e)}")
    
    def backup_server_properties(self, properties_file):
        backup_dir = os.path.join(self.panel.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"server.properties.{timestamp}.bak")
        
        try:
            shutil.copy2(properties_file, backup_file)
            self.panel.log_message(f"服务器属性文件已备份到: {backup_file}")
        except Exception as e:
            self.panel.log_message(f"备份服务器属性文件时出错: {str(e)}")
    
    def validate_server_properties(self, properties):
        if 'server-port' in properties:
            port = properties['server-port']
            if not port.isdigit() or not (1 <= int(port) <= 65535):
                self.panel.log_message("警告: 服务器端口号无效，将使用默认值 25565")
                properties['server-port'] = "25565"
        
        if 'max-players' in properties:
            max_players = properties['max-players']
            if not max_players.isdigit() or int(max_players) < 1:
                self.panel.log_message("警告: 最大玩家数无效，将使用默认值 20")
                properties['max-players'] = "20"
        
        if 'view-distance' in properties:
            view_distance = properties['view-distance']
            if not view_distance.isdigit() or not (3 <= int(view_distance) <= 32):
                self.panel.log_message("警告: 视图距离无效，将使用默认值 10")
                properties['view-distance'] = "10"
        
        boolean_props = ['online-mode', 'white-list', 'pvp', 'spawn-monsters', 'spawn-animals', 'spawn-npcs', 'allow-flight']
        for prop in boolean_props:
            if prop in properties and properties[prop] not in ['true', 'false']:
                self.panel.log_message(f"警告: {prop} 值无效，将使用默认值 true")
                properties[prop] = "true"
        
        if 'difficulty' in properties and properties['difficulty'] not in ['peaceful', 'easy', 'normal', 'hard']:
            self.panel.log_message("警告: 难度值无效，将使用默认值 easy")
            properties['difficulty'] = "easy"
        
        if 'gamemode' in properties and properties['gamemode'] not in ['survival', 'creative', 'adventure', 'spectator']:
            self.panel.log_message("警告: 游戏模式值无效，将使用默认值 survival")
            properties['gamemode'] = "survival"
    
    def validate_max_players_setting(self, event=None):
        value = self.panel.max_players_var.get()
        error = self.validate_max_players(value)
        self.panel.max_players_validation_var.set(error)
        return len(error) == 0
    
    def apply_max_players_setting(self):
        if not self.validate_max_players_setting():
            messagebox.showerror("验证错误", self.panel.max_players_validation_var.get())
            return
        
        value = self.panel.max_players_var.get().strip()
        
        try:
            num = int(value)
            if num > 100:
                if not messagebox.askyesno("性能警告", 
                    f"设置的最大玩家数为 {num}，超过100人可能会影响服务器性能。\n\n是否继续应用此设置？"):
                    return
            
            self.set_property("max-players", value)
            
            if "max-players" in self.panel.property_vars:
                self.panel.property_vars["max-players"].set(value)
            
            self.panel.log_message(f"最大玩家数已设置为: {value}")
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
