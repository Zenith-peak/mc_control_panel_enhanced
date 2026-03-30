import os
import configparser
from tkinter import messagebox


class ConfigManager:
    def __init__(self, panel):
        self.panel = panel
        self.config_file = "mc_panel_config.ini"
    
    def save_config(self):
        config = configparser.ConfigParser()
        
        config['PATHS'] = {
            'jar_path': self.panel.jar_path_var.get(),
            'server_dir': self.panel.server_dir_var.get(),
            'java_path': self.panel.java_path_var.get()
        }
        
        config['JAVA'] = {
            'min_memory': self.panel.min_mem_var.get(),
            'max_memory': self.panel.max_mem_var.get()
        }
        
        config['SETTINGS'] = {
            'auto_start': str(self.panel.auto_start_var.get()),
            'auto_backup': str(self.panel.auto_backup_var.get()),
            'auto_update': str(self.panel.auto_update_var.get()),
            'max_players': self.panel.max_players_var.get()
        }
        
        config['SERVER_ADDRESS'] = {
            'server_ip': self.panel.server_ip_var.get(),
            'server_port': self.panel.server_port_var.get()
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            messagebox.showinfo("成功", "设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置时出错: {str(e)}")
    
    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file, encoding='utf-8')
        except:
            config.read(self.config_file)
        
        try:
            if 'PATHS' in config:
                self.panel.jar_path_var.set(config['PATHS'].get('jar_path', 'server.jar'))
                self.panel.server_dir_var.set(config['PATHS'].get('server_dir', os.getcwd()))
                self.panel.java_path_var.set(config['PATHS'].get('java_path', 'java'))
            
            if 'JAVA' in config:
                self.panel.min_mem_var.set(config['JAVA'].get('min_memory', '1G'))
                self.panel.max_mem_var.set(config['JAVA'].get('max_memory', '2G'))
            
            if 'SETTINGS' in config:
                self.panel.auto_start_var.set(config['SETTINGS'].getboolean('auto_start', False))
                self.panel.auto_backup_var.set(config['SETTINGS'].getboolean('auto_backup', False))
                self.panel.auto_update_var.set(config['SETTINGS'].getboolean('auto_update', False))
                max_players = config['SETTINGS'].get('max_players', '20')
                if max_players:
                    self.panel.max_players_var.set(max_players)
            
            if 'SERVER_ADDRESS' in config:
                self.panel.server_ip_var.set(config['SERVER_ADDRESS'].get('server_ip', ''))
                self.panel.server_port_var.set(config['SERVER_ADDRESS'].get('server_port', '25565'))
        except Exception as e:
            print(f"加载设置时出错: {str(e)}")
