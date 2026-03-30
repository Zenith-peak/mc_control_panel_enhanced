import os
import zipfile
import json
import xml.etree.ElementTree as ET
from datetime import datetime

class PluginManager:
    def __init__(self, server_dir):
        self.server_dir = server_dir
        self.plugins_dir = os.path.join(server_dir, "plugins")
        self.plugins = []
    
    def scan_plugins(self):
        """扫描plugins目录，获取插件信息"""
        self.plugins = []
        
        if not os.path.exists(self.plugins_dir):
            return self.plugins
        
        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            
            if item.endswith('.jar'):
                plugin_info = self._parse_jar_plugin(item_path)
                if plugin_info:
                    self.plugins.append(plugin_info)
            elif os.path.isdir(item_path):
                plugin_info = self._parse_directory_plugin(item_path)
                if plugin_info:
                    self.plugins.append(plugin_info)
        
        return self.plugins
    
    def _parse_jar_plugin(self, jar_path):
        """解析jar文件获取插件信息"""
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # 尝试读取plugin.yml
                if 'plugin.yml' in jar.namelist():
                    return self._parse_plugin_yml(jar)
                # 尝试读取bungee.yml
                elif 'bungee.yml' in jar.namelist():
                    return self._parse_bungee_yml(jar)
                # 尝试读取fabric.mod.json
                elif 'fabric.mod.json' in jar.namelist():
                    return self._parse_fabric_mod(jar)
                # 尝试读取mods.toml（Forge）
                elif 'META-INF/mods.toml' in jar.namelist():
                    return self._parse_forge_mod(jar)
                else:
                    # 如果无法识别插件类型，返回基本信息
                    return {
                        'name': os.path.basename(jar_path),
                        'version': '未知',
                        'author': '未知',
                        'description': '无法解析插件信息',
                        'type': 'jar',
                        'path': jar_path,
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(jar_path)).strftime('%Y-%m-%d %H:%M:%S')
                    }
        except Exception as e:
            print(f"解析插件 {jar_path} 失败: {e}")
            return {
                'name': os.path.basename(jar_path),
                'version': '错误',
                'author': '未知',
                'description': f'解析失败: {str(e)}',
                'type': 'jar',
                'path': jar_path,
                'last_modified': datetime.fromtimestamp(os.path.getmtime(jar_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _parse_directory_plugin(self, dir_path):
        """解析目录形式的插件"""
        plugin_yml = os.path.join(dir_path, 'plugin.yml')
        if os.path.exists(plugin_yml):
            try:
                with open(plugin_yml, 'r', encoding='utf-8') as f:
                    content = f.read()
                    info = self._parse_yml_content(content)
                    if info:
                        info['type'] = 'directory'
                        info['path'] = dir_path
                        info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(dir_path)).strftime('%Y-%m-%d %H:%M:%S')
                        return info
            except Exception as e:
                print(f"解析插件目录 {dir_path} 失败: {e}")
        
        # 返回基本信息
        return {
            'name': os.path.basename(dir_path),
            'version': '未知',
            'author': '未知',
            'description': '无法解析插件信息',
            'type': 'directory',
            'path': dir_path,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(dir_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _parse_plugin_yml(self, jar):
        """解析plugin.yml文件"""
        try:
            with jar.open('plugin.yml') as f:
                content = f.read().decode('utf-8')
                info = self._parse_yml_content(content)
                if info:
                    info['type'] = 'spigot'
                    info['path'] = jar.filename
                    info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(jar.filename)).strftime('%Y-%m-%d %H:%M:%S')
                    return info
        except Exception as e:
            print(f"解析plugin.yml失败: {e}")
        return None
    
    def _parse_bungee_yml(self, jar):
        """解析bungee.yml文件"""
        try:
            with jar.open('bungee.yml') as f:
                content = f.read().decode('utf-8')
                info = self._parse_yml_content(content)
                if info:
                    info['type'] = 'bungeecord'
                    info['path'] = jar.filename
                    info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(jar.filename)).strftime('%Y-%m-%d %H:%M:%S')
                    return info
        except Exception as e:
            print(f"解析bungee.yml失败: {e}")
        return None
    
    def _parse_fabric_mod(self, jar):
        """解析fabric.mod.json文件"""
        try:
            with jar.open('fabric.mod.json') as f:
                data = json.load(f)
                info = {
                    'name': data.get('name', os.path.basename(jar.filename)),
                    'version': data.get('version', '未知'),
                    'description': data.get('description', ''),
                    'type': 'fabric'
                }
                # 处理作者信息
                authors = data.get('authors', [])
                if authors:
                    if isinstance(authors, list):
                        info['author'] = ', '.join(authors)
                    else:
                        info['author'] = authors
                else:
                    info['author'] = '未知'
                
                info['path'] = jar.filename
                info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(jar.filename)).strftime('%Y-%m-%d %H:%M:%S')
                return info
        except Exception as e:
            print(f"解析fabric.mod.json失败: {e}")
        return None
    
    def _parse_forge_mod(self, jar):
        """解析META-INF/mods.toml文件"""
        try:
            with jar.open('META-INF/mods.toml') as f:
                content = f.read().decode('utf-8')
                # 简单解析mods.toml
                info = {
                    'name': '未知',
                    'version': '未知',
                    'author': '未知',
                    'description': '',
                    'type': 'forge'
                }
                
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('modId='):
                        info['name'] = line.split('=')[1].strip('"')
                    elif line.startswith('version='):
                        info['version'] = line.split('=')[1].strip('"')
                    elif line.startswith('displayName='):
                        info['name'] = line.split('=')[1].strip('"')
                    elif line.startswith('authors='):
                        info['author'] = line.split('=')[1].strip('"')
                    elif line.startswith('description='):
                        info['description'] = line.split('=')[1].strip('"')
                
                info['path'] = jar.filename
                info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(jar.filename)).strftime('%Y-%m-%d %H:%M:%S')
                return info
        except Exception as e:
            print(f"解析mods.toml失败: {e}")
        return None
    
    def _parse_yml_content(self, content):
        """解析YML内容"""
        info = {
            'name': '未知',
            'version': '未知',
            'author': '未知',
            'description': ''
        }
        
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('name:'):
                info['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('version:'):
                info['version'] = line.split(':', 1)[1].strip()
            elif line.startswith('authors:'):
                # 处理列表形式的作者
                if '[' in line:
                    authors = line.split('[', 1)[1].split(']')[0]
                    info['author'] = ', '.join([a.strip() for a in authors.split(',')])
                else:
                    info['author'] = line.split(':', 1)[1].strip()
            elif line.startswith('author:'):
                info['author'] = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                info['description'] = line.split(':', 1)[1].strip()
        
        return info
    
    def get_plugin_count(self):
        """获取插件数量"""
        return len(self.plugins)
    
    def get_plugin_by_name(self, name):
        """根据名称获取插件信息"""
        for plugin in self.plugins:
            if plugin['name'] == name:
                return plugin
        return None
