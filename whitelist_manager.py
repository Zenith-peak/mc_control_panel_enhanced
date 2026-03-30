import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog


class WhitelistManager:
    def __init__(self, panel):
        self.panel = panel
    
    def add_to_whitelist(self):
        player = self.panel.whitelist_player_var.get().strip()
        if not player:
            messagebox.showwarning("警告", "请输入玩家名称")
            return
        
        self.panel.send_server_command(f"whitelist add {player}")
        self.panel.whitelist.append((player, datetime.now().strftime("%Y-%m-%d")))
        self.panel.whitelist_player_var.set("")
        self.load_whitelist()
        messagebox.showinfo("成功", f"已将玩家 {player} 添加到白名单")
    
    def remove_from_whitelist(self):
        selection = self.panel.whitelist_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个玩家")
            return
        
        player = self.panel.whitelist_tree.item(selection[0])['values'][0]
        self.panel.send_server_command(f"whitelist remove {player}")
        
        self.panel.whitelist = [wl for wl in self.panel.whitelist if wl[0] != player]
        
        self.load_whitelist()
        messagebox.showinfo("成功", f"已从白名单移除玩家: {player}")
    
    def reload_whitelist(self):
        self.panel.send_server_command("whitelist reload")
        messagebox.showinfo("成功", "白名单已重载")
    
    def enable_whitelist(self):
        self.panel.send_server_command("whitelist on")
        self.panel.set_property("white-list", "true")
        messagebox.showinfo("成功", "白名单已启用")
    
    def disable_whitelist(self):
        self.panel.send_server_command("whitelist off")
        self.panel.set_property("white-list", "false")
        messagebox.showinfo("成功", "白名单已禁用")
    
    def load_whitelist(self):
        for item in self.panel.whitelist_tree.get_children():
            self.panel.whitelist_tree.delete(item)
        
        for name, created in self.panel.whitelist:
            self.panel.whitelist_tree.insert("", tk.END, values=(name, created))
        
        if hasattr(self.panel, 'op_player_combo'):
            self.panel.update_player_combo()
    
    def export_whitelist(self):
        filename = filedialog.asksaveasfilename(
            title="导出白名单",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("玩家名称,添加日期\n")
                    for name, created in self.panel.whitelist:
                        f.write(f"{name},{created}\n")
                messagebox.showinfo("成功", f"白名单已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败: {str(e)}")
