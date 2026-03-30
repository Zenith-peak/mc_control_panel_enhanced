import psutil
import platform
from datetime import datetime

class PerformanceManager:
    """
    性能监控模块，负责系统和服务器性能数据的收集和管理
    """
    def __init__(self):
        """
        初始化性能监控器
        """
        self.server_process = None
        self.monitoring = False
        self.performance_data = {
            "cpu_percent": 0,
            "memory_used": 0,
            "memory_total": 0,
            "memory_percent": 0,
            "disk_used": 0,
            "disk_total": 0,
            "disk_percent": 0,
            "network_sent": 0,
            "network_recv": 0,
            "server_cpu": 0,
            "server_memory": 0
        }
        self.performance_history = []
        self.max_history_length = 50
        self.psutil_available = False
        self.platform_available = False
        
        # 检查依赖
        try:
            import psutil
            self.psutil_available = True
        except ImportError:
            pass
            
        try:
            import platform
            self.platform_available = True
        except ImportError:
            pass
    
    def start_monitoring(self, server_process):
        """
        开始监控服务器性能
        
        Args:
            server_process: 服务器进程对象
        """
        if not self.psutil_available:
            return
            
        self.server_process = server_process
        self.monitoring = True
    
    def stop_monitoring(self):
        """
        停止监控
        """
        self.monitoring = False
        self.server_process = None
    
    def get_performance_data(self):
        """
        获取性能数据
        
        Returns:
            dict: 包含性能指标的字典
        """
        if not self.psutil_available:
            return self.performance_data
            
        try:
            # 系统CPU使用率
            self.performance_data["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            self.performance_data["memory_used"] = memory.used / (1024 ** 3)
            self.performance_data["memory_total"] = memory.total / (1024 ** 3)
            self.performance_data["memory_percent"] = memory.percent
            
            # 磁盘使用情况
            import os
            server_dir = os.getcwd()
            disk = psutil.disk_usage(server_dir)
            self.performance_data["disk_used"] = disk.used / (1024 ** 3)
            self.performance_data["disk_total"] = disk.total / (1024 ** 3)
            self.performance_data["disk_percent"] = disk.percent
            
            # 网络使用情况
            net_io = psutil.net_io_counters()
            self.performance_data["network_sent"] = net_io.bytes_sent / (1024 ** 2)
            self.performance_data["network_recv"] = net_io.bytes_recv / (1024 ** 2)
            
            # 服务器进程资源使用
            if self.server_process and self.server_process.poll() is None:
                try:
                    server_pid = self.server_process.pid
                    server_process = psutil.Process(server_pid)
                    
                    server_cpu = server_process.cpu_percent()
                    server_memory = server_process.memory_info().rss / (1024 ** 2)
                    
                    self.performance_data["server_cpu"] = server_cpu
                    self.performance_data["server_memory"] = server_memory
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.performance_data["server_cpu"] = 0
                    self.performance_data["server_memory"] = 0
                    
        except Exception as e:
            print(f"获取性能数据时出错: {e}")
            
        # 添加到历史记录
        self.performance_history.append({
            "timestamp": datetime.now(),
            "cpu": self.performance_data["cpu_percent"],
            "memory": self.performance_data["memory_percent"],
            "server_cpu": self.performance_data.get("server_cpu", 0),
            "server_memory": self.performance_data.get("server_memory", 0)
        })
        
        # 限制历史记录长度
        if len(self.performance_history) > self.max_history_length:
            self.performance_history.pop(0)
            
        return self.performance_data
    
    def get_performance_history(self):
        """
        获取性能历史数据
        
        Returns:
            list: 性能历史记录列表
        """
        return self.performance_history
    
    def get_system_info(self):
        """
        获取系统信息
        
        Returns:
            dict: 系统信息字典
        """
        system_info = {}
        
        if self.platform_available:
            try:
                system_info["os"] = f"{platform.system()} {platform.release()}"
                system_info["cpu"] = platform.processor()
            except Exception as e:
                print(f"获取系统信息时出错: {e}")
        
        return system_info
