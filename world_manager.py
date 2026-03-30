import os
import shutil
import threading
import time
import zipfile
import tempfile
import webbrowser
from datetime import datetime
from tkinter import ttk, messagebox, simpledialog, filedialog
import tkinter as tk


class WorldManager:
    def __init__(self, panel):
        self.panel = panel
        self.gamerule_vars = {}
    
    def create_backup(self):
        backup_name = simpledialog.askstring("创建备份", "请输入备份名称:", parent=self.panel.root)
        if backup_name:
            progress_window = tk.Toplevel(self.panel.root)
            progress_window.title("创建备份")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            x = (self.panel.root.winfo_width() // 2) - 150
            y = (self.panel.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            progress_label = ttk.Label(progress_window, text="正在创建备份...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def backup_thread():
                try:
                    self.panel.send_server_command("save-all")
                    self.panel.log_message(f"正在创建备份: {backup_name}")
                    
                    backup_dir = os.path.join(self.panel.server_dir_var.get(), "backups")
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    
                    world_dir = os.path.join(self.panel.server_dir_var.get(), "world")
                    if os.path.exists(world_dir):
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = os.path.join(backup_dir, f"{backup_name}_{timestamp}")
                        shutil.copytree(world_dir, backup_path)
                        self.panel.log_message(f"备份已创建: {backup_path}")
                        
                        self.panel.root.after(0, self.refresh_backup_list)
                        self.panel.root.after(0, lambda: messagebox.showinfo("成功", f"备份 {backup_name} 创建成功"))
                    else:
                        self.panel.root.after(0, lambda: messagebox.showerror("错误", "找不到世界目录"))
                except Exception as e:
                    error_message = f"创建备份时出错: {str(e)}"
                    self.panel.log_message(error_message)
                    self.panel.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    self.panel.root.after(0, progress_window.destroy)
            
            threading.Thread(target=backup_thread, daemon=True).start()
    
    def restore_backup(self):
        backup_dir = os.path.join(self.panel.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            messagebox.showerror("错误", "备份目录不存在")
            return
        
        backups = [d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))]
        if not backups:
            messagebox.showerror("错误", "没有找到备份")
            return
        
        backup_list_window = tk.Toplevel(self.panel.root)
        backup_list_window.title("选择备份")
        backup_list_window.geometry("400x300")
        
        tk.Label(backup_list_window, text="请选择要恢复的备份:").pack(pady=10)
        
        backup_listbox = tk.Listbox(backup_list_window)
        backup_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for backup in sorted(backups, reverse=True):
            backup_listbox.insert(tk.END, backup)
        
        def confirm_restore():
            selection = backup_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请选择一个备份")
                return
            
            backup_name = backup_listbox.get(selection[0])
            backup_list_window.destroy()
            
            result = messagebox.askyesno("确认", f"确定要恢复备份 {backup_name} 吗？当前世界将被覆盖！")
            if result:
                self.panel.log_message(f"正在恢复备份: {backup_name}")
                
                if self.panel.server_manager.server_running:
                    self.panel.stop_server()
                    self.panel.root.after(5000, lambda: self.do_restore_backup(os.path.join(backup_dir, backup_name)))
                else:
                    self.do_restore_backup(os.path.join(backup_dir, backup_name))
        
        tk.Button(backup_list_window, text="恢复选中的备份", command=confirm_restore).pack(pady=10)
    
    def do_restore_backup(self, backup_path):
        progress_window = tk.Toplevel(self.panel.root)
        progress_window.title("恢复备份")
        progress_window.geometry("300x100")
        progress_window.resizable(False, False)
        
        x = (self.panel.root.winfo_width() // 2) - 150
        y = (self.panel.root.winfo_height() // 2) - 50
        progress_window.geometry(f"300x100+{x}+{y}")
        
        progress_label = ttk.Label(progress_window, text="正在恢复备份...", font=('微软雅黑', 10))
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        progress_bar.start()
        
        def restore_thread():
            try:
                world_dir = os.path.join(self.panel.server_dir_var.get(), "world")
                if os.path.exists(world_dir):
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_current = os.path.join(self.panel.server_dir_var.get(), "backups", f"pre_restore_{timestamp}")
                    shutil.copytree(world_dir, backup_current)
                
                if os.path.exists(world_dir):
                    shutil.rmtree(world_dir)
                
                shutil.copytree(backup_path, world_dir)
                
                self.panel.log_message(f"备份 {os.path.basename(backup_path)} 恢复成功")
                
                if self.panel.auto_start_var.get():
                    self.panel.root.after(2000, self.panel.start_server)
                
                self.panel.root.after(0, lambda: messagebox.showinfo("成功", f"备份 {os.path.basename(backup_path)} 恢复成功"))
            except Exception as e:
                error_message = f"恢复备份时出错: {str(e)}"
                self.panel.log_message(error_message)
                self.panel.root.after(0, lambda: messagebox.showerror("错误", error_message))
            finally:
                self.panel.root.after(0, progress_window.destroy)
        
        threading.Thread(target=restore_thread, daemon=True).start()
    
    def open_backup_folder(self):
        backup_dir = os.path.join(self.panel.server_dir_var.get(), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        webbrowser.open(backup_dir)
    
    def auto_backup_settings(self):
        settings_window = tk.Toplevel(self.panel.root)
        settings_window.title("自动备份设置")
        settings_window.geometry("400x200")
        
        tk.Label(settings_window, text="自动备份设置", font=("微软雅黑", "Times New Roman", 12, "bold")).pack(pady=10)
        
        interval_frame = tk.Frame(settings_window)
        interval_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(interval_frame, text="备份间隔:").pack(side=tk.LEFT)
        interval_var = tk.StringVar(value="60")
        interval_entry = tk.Entry(interval_frame, textvariable=interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(interval_frame, text="分钟").pack(side=tk.LEFT)
        
        max_backups_frame = tk.Frame(settings_window)
        max_backups_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(max_backups_frame, text="最大备份数量:").pack(side=tk.LEFT)
        max_backups_var = tk.StringVar(value="10")
        max_backups_entry = tk.Entry(max_backups_frame, textvariable=max_backups_var, width=10)
        max_backups_entry.pack(side=tk.LEFT, padx=5)
        
        def save_settings():
            messagebox.showinfo("成功", "自动备份设置已保存")
            settings_window.destroy()
        
        tk.Button(settings_window, text="保存设置", command=save_settings).pack(pady=20)
    
    def set_gamerule(self, rule, value):
        self.panel.send_server_command(f"gamerule {rule} {value}")
    
    def set_spawn_point(self):
        x = simpledialog.askinteger("设置出生点", "X坐标:", parent=self.panel.root)
        y = simpledialog.askinteger("设置出生点", "Y坐标:", parent=self.panel.root)
        z = simpledialog.askinteger("设置出生点", "Z坐标:", parent=self.panel.root)
        
        if x is not None and y is not None and z is not None:
            success = self.panel.send_server_command(f"setworldspawn {x} {y} {z}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法设置出生点")
    
    def change_game_mode(self):
        mode_window = tk.Toplevel(self.panel.root)
        mode_window.title("更改游戏模式")
        mode_window.geometry("300x200")
        mode_window.resizable(False, False)
        
        game_modes = {
            "生存": "survival",
            "创造": "creative",
            "冒险": "adventure",
            "旁观者": "spectator"
        }
        
        ttk.Label(mode_window, text="选择游戏模式:", font=('微软雅黑', 'Times New Roman', 12)).pack(pady=20)
        
        selected_mode = tk.StringVar(value="生存")
        mode_combo = ttk.Combobox(mode_window, textvariable=selected_mode, values=list(game_modes.keys()), state="readonly", width=15)
        mode_combo.pack(pady=10)
        
        def confirm_selection():
            chinese_mode = selected_mode.get()
            english_mode = game_modes[chinese_mode]
            success = self.panel.send_server_command(f"defaultgamemode {english_mode}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法更改游戏模式")
            self.panel.set_property("gamemode", english_mode)
            mode_window.destroy()
        
        ttk.Button(mode_window, text="确认", command=confirm_selection).pack(pady=20)
    
    def change_difficulty(self):
        difficulty_window = tk.Toplevel(self.panel.root)
        difficulty_window.title("更改难度")
        difficulty_window.geometry("300x200")
        difficulty_window.resizable(False, False)
        
        difficulties = {
            "和平": "peaceful",
            "简单": "easy",
            "普通": "normal",
            "困难": "hard"
        }
        
        ttk.Label(difficulty_window, text="选择难度:", font=('微软雅黑', 'Times New Roman', 12)).pack(pady=20)
        
        selected_difficulty = tk.StringVar(value="和平")
        difficulty_combo = ttk.Combobox(difficulty_window, textvariable=selected_difficulty, values=list(difficulties.keys()), state="readonly", width=15)
        difficulty_combo.pack(pady=10)
        
        def confirm_selection():
            chinese_difficulty = selected_difficulty.get()
            english_difficulty = difficulties[chinese_difficulty]
            success = self.panel.send_server_command(f"difficulty {english_difficulty}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法更改难度")
            self.panel.set_property("difficulty", english_difficulty)
            difficulty_window.destroy()
        
        ttk.Button(difficulty_window, text="确认", command=confirm_selection).pack(pady=20)
    
    def set_time(self):
        time_str = simpledialog.askstring("设置时间", "请输入时间 (day, night, noon, midnight 或 0-24000):", parent=self.panel.root)
        if time_str:
            success = self.panel.send_server_command(f"time set {time_str}")
            if not success:
                messagebox.showwarning("警告", "服务器未运行，无法设置时间")
    
    def refresh_backup_list(self):
        try:
            if hasattr(self.panel, 'backup_tree'):
                for item in self.panel.backup_tree.get_children():
                    self.panel.backup_tree.delete(item)
                
                backup_dir = os.path.join(os.getcwd(), "backups")
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                for filename in os.listdir(backup_dir):
                    if filename.endswith(".zip") or filename.endswith(".rar"):
                        file_path = os.path.join(backup_dir, filename)
                        file_stat = os.stat(file_path)
                        
                        file_size = file_stat.st_size
                        size_str = self.format_file_size(file_size)
                        
                        create_time = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                        
                        if "autobackup" in filename.lower():
                            backup_type = "自动"
                        else:
                            backup_type = "手动"
                        
                        self.panel.backup_tree.insert("", tk.END, values=(filename, create_time, size_str, backup_type))
        except Exception as e:
            messagebox.showerror("错误", f"刷新备份列表时出错: {str(e)}")
    
    def delete_backup(self):
        if hasattr(self.panel, 'backup_tree'):
            selection = self.panel.backup_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请选择要删除的备份")
                return
            
            item = selection[0]
            backup_name = self.panel.backup_tree.item(item)['values'][0]
            
            result = messagebox.askyesno("确认", f"确定要删除备份 {backup_name} 吗？")
            if result:
                try:
                    backup_path = os.path.join(os.getcwd(), "backups", backup_name)
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                        self.refresh_backup_list()
                        messagebox.showinfo("成功", f"备份 {backup_name} 已删除")
                    else:
                        messagebox.showwarning("警告", "备份文件不存在")
                except Exception as e:
                    messagebox.showerror("错误", f"删除备份时出错: {str(e)}")
    
    def export_backup(self):
        if hasattr(self.panel, 'backup_tree'):
            selection = self.panel.backup_tree.selection()
            if not selection:
                messagebox.showwarning("警告", "请选择要导出的备份")
                return
            
            item = selection[0]
            backup_name = self.panel.backup_tree.item(item)['values'][0]
            backup_path = os.path.join(os.getcwd(), "backups", backup_name)
            
            if not os.path.exists(backup_path):
                messagebox.showwarning("警告", "备份文件不存在")
                return
            
            export_path = filedialog.asksaveasfilename(
                title="导出备份",
                defaultextension=".zip",
                initialfile=backup_name,
                filetypes=[("ZIP files", "*.zip"), ("RAR files", "*.rar"), ("All files", "*.*")]
            )
            
            if export_path:
                try:
                    shutil.copy2(backup_path, export_path)
                    messagebox.showinfo("成功", f"备份已导出到: {export_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出备份时出错: {str(e)}")
    
    def import_world(self):
        import_path = filedialog.askopenfilename(
            title="导入世界",
            filetypes=[("ZIP files", "*.zip"), ("RAR files", "*.rar"), ("All files", "*.*")]
        )
        
        if import_path:
            if hasattr(self.panel, 'server_manager') and self.panel.server_manager.server_running:
                result = messagebox.askyesno("警告", "服务器正在运行，导入世界需要停止服务器。是否继续？")
                if not result:
                    return
                self.panel.server_manager.stop_server()
                time.sleep(2)
            
            progress_window = tk.Toplevel(self.panel.root)
            progress_window.title("导入世界")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            x = (self.panel.root.winfo_width() // 2) - 150
            y = (self.panel.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            progress_label = ttk.Label(progress_window, text="正在导入世界...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def import_thread():
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        with zipfile.ZipFile(import_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        
                        world_folders = []
                        for root, dirs, files in os.walk(temp_dir):
                            if "level.dat" in files:
                                world_folders.append(root)
                        
                        if not world_folders:
                            self.panel.root.after(0, lambda: messagebox.showwarning("警告", "未找到有效的世界文件夹"))
                            return
                        
                        world_source = world_folders[0]
                        world_dest = os.path.join(self.panel.server_dir_var.get(), "world")
                        
                        if os.path.exists(world_dest):
                            backup_name = f"world_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            backup_path = os.path.join(self.panel.server_dir_var.get(), "backups", backup_name)
                            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                            shutil.make_archive(backup_path, 'zip', world_dest)
                        
                        if os.path.exists(world_dest):
                            shutil.rmtree(world_dest)
                        
                        shutil.copytree(world_source, world_dest)
                        
                        self.panel.log_message("世界导入成功")
                        self.panel.root.after(0, lambda: messagebox.showinfo("成功", "世界导入成功"))
                except Exception as e:
                    error_message = f"导入世界时出错: {str(e)}"
                    self.panel.log_message(error_message)
                    self.panel.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    self.panel.root.after(0, progress_window.destroy)
            
            threading.Thread(target=import_thread, daemon=True).start()
    
    def export_world(self):
        if hasattr(self.panel, 'server_manager') and self.panel.server_manager.server_running:
            self.panel.send_server_command("save-all")
            time.sleep(1)
        
        export_path = filedialog.asksaveasfilename(
            title="导出世界",
            defaultextension=".zip",
            initialfile=f"world_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        
        if export_path:
            progress_window = tk.Toplevel(self.panel.root)
            progress_window.title("导出世界")
            progress_window.geometry("300x100")
            progress_window.resizable(False, False)
            
            x = (self.panel.root.winfo_width() // 2) - 150
            y = (self.panel.root.winfo_height() // 2) - 50
            progress_window.geometry(f"300x100+{x}+{y}")
            
            progress_label = ttk.Label(progress_window, text="正在导出世界...", font=('微软雅黑', 10))
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(fill=tk.X, padx=20, pady=10)
            progress_bar.start()
            
            def export_thread():
                try:
                    world_path = os.path.join(self.panel.server_dir_var.get(), "world")
                    if not os.path.exists(world_path):
                        self.panel.root.after(0, lambda: messagebox.showwarning("警告", "世界文件夹不存在"))
                        return
                    
                    shutil.make_archive(export_path.replace('.zip', ''), 'zip', world_path)
                    
                    self.panel.log_message(f"世界已导出到: {export_path}")
                    self.panel.root.after(0, lambda: messagebox.showinfo("成功", f"世界已导出到: {export_path}"))
                except Exception as e:
                    error_message = f"导出世界时出错: {str(e)}"
                    self.panel.log_message(error_message)
                    self.panel.root.after(0, lambda: messagebox.showerror("错误", error_message))
                finally:
                    self.panel.root.after(0, progress_window.destroy)
            
            threading.Thread(target=export_thread, daemon=True).start()
    
    def apply_all_gamerules(self):
        try:
            applied_rules = []
            for rule, var in self.gamerule_vars.items():
                value = var.get()
                self.panel.send_server_command(f"gamerule {rule} {value}")
                applied_rules.append(f"{rule}: {value}")
            
            message = "已应用以下游戏规则:\n" + "\n".join(applied_rules)
            messagebox.showinfo("成功", message)
        except Exception as e:
            messagebox.showerror("错误", f"应用游戏规则时出错: {str(e)}")
    
    def reset_gamerules(self):
        default_rules = {
            "keepInventory": "false",
            "mobGriefing": "true",
            "doDaylightCycle": "true",
            "doWeatherCycle": "true",
            "doFireTick": "true",
            "naturalRegeneration": "true",
            "commandBlockOutput": "true",
            "doTileDrops": "true",
            "doMobSpawning": "true"
        }
        
        for rule, default_value in default_rules.items():
            if rule in self.gamerule_vars:
                self.gamerule_vars[rule].set(default_value)
        
        messagebox.showinfo("成功", "游戏规则已重置为默认值")
    
    def format_file_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
