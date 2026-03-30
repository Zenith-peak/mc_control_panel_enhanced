import subprocess
import threading
import time
import os
import socket
from datetime import datetime

class ServerManager:
    """
    服务器管理模块，负责服务器的启动、停止、重启等核心功能
    """
    def __init__(self, control_panel):
        """
        初始化服务器管理器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.server_process = None
        self.server_running = False
        self.output_thread = None
        self.simulation_thread = None
        
    def start_server(self):
        """
        启动服务器
        
        Returns:
            bool: 启动是否成功
        """
        jar_path = self.control_panel.jar_path_var.get()
        if not os.path.exists(jar_path):
            self.control_panel.log_message(f"错误: 找不到服务器JAR文件: {jar_path}")
            return False
        
        # 检查服务器目录
        server_dir = self.control_panel.server_dir_var.get()
        if not os.path.exists(server_dir):
            try:
                os.makedirs(server_dir)
            except Exception as e:
                self.control_panel.log_message(f"错误: 无法创建服务器目录: {str(e)}")
                return False
        
        # 构建启动命令 - 修复中文显示问题
        min_mem = self.control_panel.min_mem_var.get()
        max_mem = self.control_panel.max_mem_var.get()
        java_path = self.control_panel.java_path_var.get()
        
        # 添加UTF-8编码参数确保中文正常显示
        command = f'"{java_path}" -Xms{min_mem} -Xmx{max_mem} -Dfile.encoding=UTF-8 -Dsun.jnu.encoding=UTF-8 -jar "{jar_path}" nogui'
        
        try:
            # 切换到服务器目录
            os.chdir(server_dir)
            
            # 使用支持UTF-8的环境启动服务器
            env = os.environ.copy()
            env['JAVA_TOOL_OPTIONS'] = '-Dfile.encoding=UTF-8'
            
            # 修复中文显示问题 - 使用正确的编码
            self.server_process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                shell=True,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
            
            self.server_running = True
            self.control_panel.status_var.set("服务器状态: 运行中")
            self.control_panel.start_button.config(state="disabled")
            self.control_panel.stop_button.config(state="normal")
            self.control_panel.restart_button.config(state="normal")
            
            # 启动线程读取服务器输出
            self.output_thread = threading.Thread(target=self.read_output)
            self.output_thread.daemon = True
            self.output_thread.start()
            
            # 启动性能监控
            if self.control_panel.performance_monitor:
                self.control_panel.performance_monitor.start_monitoring(self.server_process)
            
            # 启动玩家位置和延迟模拟
            self.start_player_simulation()
            
            self.control_panel.log_message("服务器已启动")
            
            # 启动定期数据更新
            self.control_panel.start_periodic_updates()
            
            return True
        except Exception as e:
            self.control_panel.log_message(f"错误: 启动服务器时出错: {str(e)}")
            return False
    
    def stop_server(self):
        """
        停止服务器
        
        Returns:
            bool: 停止是否成功
        """
        if self.server_process and self.server_running:
            try:
                self.control_panel.send_server_command("stop")
                
                # 停止性能监控
                if self.control_panel.performance_monitor:
                    self.control_panel.performance_monitor.stop_monitoring()
                
                # 停止玩家模拟
                self.stop_player_simulation()
                
                # 等待进程结束
                def wait_for_stop():
                    try:
                        self.server_process.wait(timeout=30)
                        self.control_panel.root.after(0, self.server_stopped)
                    except subprocess.TimeoutExpired:
                        self.server_process.terminate()
                        self.control_panel.root.after(0, self.server_stopped)
                
                stop_thread = threading.Thread(target=wait_for_stop)
                stop_thread.daemon = True
                stop_thread.start()
                
                return True
            except Exception as e:
                self.control_panel.log_message(f"错误: 停止服务器时出错: {str(e)}")
                return False
        return False
    
    def restart_server(self):
        """
        重启服务器
        
        Returns:
            bool: 重启是否成功
        """
        self.control_panel.log_message("正在重启服务器...")
        if self.stop_server():
            self.control_panel.root.after(5000, self.start_server)
            return True
        return False
    
    def read_output(self):
        """
        读取服务器输出 - 修复中文显示问题
        """
        while self.server_process and self.server_running:
            try:
                output = self.server_process.stdout.readline()
                if output:
                    # 直接使用UTF-8，因为我们已经设置了编码
                    decoded_output = output
                    self.control_panel.root.after(0, self.control_panel.process_output, decoded_output.strip())
                elif self.server_process.poll() is not None:
                    break
            except Exception as e:
                self.control_panel.log_message(f"错误: 读取输出时出错: {e}")
                break
        
        # 服务器进程已结束
        if self.server_running:
            self.control_panel.root.after(0, self.server_stopped_unexpectedly)
    
    def server_stopped(self):
        """
        服务器正常停止
        """
        self.server_running = False
        self.control_panel.status_var.set("服务器状态: 已停止")
        self.control_panel.start_button.config(state="normal")
        self.control_panel.stop_button.config(state="disabled")
        self.control_panel.restart_button.config(state="disabled")
        self.control_panel.log_message("服务器已停止")
        
        # 清空在线玩家列表
        self.control_panel.players_online = []
        self.control_panel.update_players_display()
    
    def server_stopped_unexpectedly(self):
        """
        服务器意外停止
        """
        self.server_running = False
        self.control_panel.status_var.set("服务器状态: 已停止 (意外退出)")
        self.control_panel.start_button.config(state="normal")
        self.control_panel.stop_button.config(state="disabled")
        self.control_panel.restart_button.config(state="disabled")
        self.control_panel.log_message("服务器进程意外退出")
        
        # 清空在线玩家列表
        self.control_panel.players_online = []
        self.control_panel.update_players_display()
    
    def start_player_simulation(self):
        """
        启动玩家位置和延迟监控，通过服务器命令获取实际数据
        """
        if not self.server_running:
            return
            
        def monitor_player_data():
            while self.server_running:
                for player in self.control_panel.players_online:
                    # 发送命令获取玩家位置
                    self.send_server_command(f"data get entity {player} Pos")
                    # 发送命令获取玩家延迟（通过服务器日志获取）
                    # 注意：Minecraft 服务器本身不会直接提供延迟命令，需要通过日志分析或插件
                    # 这里我们暂时使用模拟值，实际项目中可以通过分析服务器日志来获取延迟
                    ping = max(10, min(500, self.control_panel.message_manager.get_player_ping(player) + (ord(player[0]) % 20 - 10)))
                    self.control_panel.message_manager.update_player_ping(player, ping)
                
                time.sleep(5)  # 每5秒更新一次，避免命令发送过于频繁
        
        self.simulation_thread = threading.Thread(target=monitor_player_data)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
    
    def stop_player_simulation(self):
        """
        停止玩家模拟
        """
        self.server_running = False
    
    def send_server_command(self, command):
        """
        发送命令到服务器进程
        
        Args:
            command: 要发送的命令
            
        Returns:
            bool: 发送是否成功
        """
        if self.server_process and self.server_running:
            try:
                # 确保命令使用UTF-8编码发送
                encoded_command = command + "\n"
                self.server_process.stdin.write(encoded_command)
                self.server_process.stdin.flush()
                self.control_panel.log_message(f"> {command}")
                
                # 如果命令是管理员相关操作，刷新数据
                if command.startswith(('deop ', 'pardon ', 'unmute ', 'whitelist remove ')):
                    # 延迟一小段时间后刷新数据，确保服务器已处理命令
                    self.control_panel.root.after(1000, self.control_panel.refresh_admin_panel_data)
                    
                # 如果命令是tell/msg，记录消息
                if command.startswith(('/tell ', '/msg ')):
                    parts = command.split(' ', 2)
                    if len(parts) >= 3:
                        player = parts[1]
                        message = parts[2]
                        self.control_panel.message_manager.add_message(player, message, is_server=True)
                        
                return True
            except Exception as e:
                self.control_panel.log_message(f"错误: 发送命令时出错: {str(e)}")
                return False
        else:
            self.control_panel.log_message("警告: 服务器未运行，无法发送命令")
            return False
