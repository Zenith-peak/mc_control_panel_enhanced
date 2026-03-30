import os
import re
import zipfile
import json
from datetime import datetime
import tkinter as tk

class VersionDetector:
    """
    服务器版本识别模块，通过server.jar文件或服务器输出来识别版本
    """
    
    def __init__(self, control_panel):
        """
        初始化版本检测器
        
        Args:
            control_panel: 主控制面板实例
        """
        self.control_panel = control_panel
        self.server_version = "未知"
        self.detected_by = "未检测"
    
    def detect_version_from_jar(self, jar_path):
        """
        从server.jar文件中检测版本
        
        Args:
            jar_path: server.jar文件路径
            
        Returns:
            str: 服务器版本号
        """
        try:
            if not os.path.exists(jar_path):
                return "未知"
            
            # 打开jar文件
            with zipfile.ZipFile(jar_path, 'r') as zf:
                # 尝试从版本文件中读取
                version_files = ['version.json', 'META-INF/versions/1.16.5/version.json']
                
                for version_file in version_files:
                    try:
                        if version_file in zf.namelist():
                            with zf.open(version_file) as f:
                                version_data = json.load(f)
                                if 'id' in version_data:
                                    self.server_version = version_data['id']
                                    self.detected_by = "JAR文件"
                                    return self.server_version
                    except Exception:
                        continue
                
                # 尝试从manifest.json中读取
                if 'META-INF/MANIFEST.MF' in zf.namelist():
                    with zf.open('META-INF/MANIFEST.MF') as f:
                        manifest_content = f.read().decode('utf-8')
                        version_match = re.search(r'Implementation-Version: (.+)', manifest_content)
                        if version_match:
                            self.server_version = version_match.group(1)
                            self.detected_by = "JAR文件"
                            return self.server_version
            
            return "未知"
        except Exception as e:
            print(f"从JAR文件检测版本时出错: {e}")
            return "未知"
    
    def detect_version_from_output(self, output):
        """
        从服务器输出中检测版本
        
        Args:
            output: 服务器输出文本
            
        Returns:
            str: 服务器版本号
        """
        try:
            # 匹配服务器启动时的版本信息
            patterns = [
                r'Minecraft server version: (.+)',
                r'Starting Minecraft server version (.+)',
                r'[0-9:]+\s*\[Server thread/INFO\]:\s*Starting minecraft server version (.+)',
                r'version: (.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    self.server_version = match.group(1).strip()
                    self.detected_by = "服务器输出"
                    return self.server_version
            
            return "未知"
        except Exception as e:
            print(f"从服务器输出检测版本时出错: {e}")
            return "未知"
    
    def get_version(self):
        """
        获取检测到的服务器版本
        
        Returns:
            str: 服务器版本号
        """
        return self.server_version
    
    def get_detection_method(self):
        """
        获取版本检测的方法
        
        Returns:
            str: 检测方法
        """
        return self.detected_by
    
    def update_version_display(self):
        """
        更新界面上的版本显示
        """
        if hasattr(self.control_panel, 'version_var'):
            version_info = f"服务器版本: {self.server_version} ({self.detected_by})"
            self.control_panel.version_var.set(version_info)
    
    def detect_version(self):
        """
        综合检测服务器版本
        
        Returns:
            str: 服务器版本号
        """
        # 首先尝试从JAR文件检测
        jar_path = self.control_panel.jar_path_var.get()
        version_from_jar = self.detect_version_from_jar(jar_path)
        
        if version_from_jar != "未知":
            self.update_version_display()
            return version_from_jar
        
        # 如果JAR文件检测失败，尝试从服务器日志检测
        if hasattr(self.control_panel, 'log_text'):
            log_content = self.control_panel.log_text.get(1.0, tk.END)
            version_from_log = self.detect_version_from_output(log_content)
            if version_from_log != "未知":
                self.update_version_display()
                return version_from_log
        
        self.update_version_display()
        return "未知"
