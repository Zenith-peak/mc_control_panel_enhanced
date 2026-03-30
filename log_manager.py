import os
from datetime import datetime
from tkinter import messagebox, simpledialog, filedialog


class LogManager:
    def __init__(self, panel):
        self.panel = panel
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def save_server_logs(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.logs_dir, f'server_log_{timestamp}.txt')
            
            log_content = self.panel.log_text.get(1.0, 'end')
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"服务器日志已保存到: {log_file}")
        except Exception as e:
            print(f"保存服务器日志时出错: {e}")
    
    def save_performance_logs(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(self.logs_dir, f'performance_log_{timestamp}.txt')
            
            if hasattr(self.panel, 'performance_monitor'):
                history = self.panel.performance_monitor.get_performance_history()
                
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("性能历史数据\n")
                    f.write("=" * 60 + "\n")
                    for record in history:
                        ts = record['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                        cpu = record['cpu']
                        memory = record['memory']
                        server_cpu = record.get('server_cpu', 0)
                        server_memory = record.get('server_memory', 0)
                        
                        line = f"[{ts}] CPU: {cpu:.1f}% | 内存: {memory:.1f}%"
                        if server_cpu > 0:
                            line += f" | 服务器CPU: {server_cpu:.1f}% | 服务器内存: {server_memory:.1f}MB"
                        f.write(line + "\n")
                
                print(f"性能日志已保存到: {log_file}")
        except Exception as e:
            print(f"保存性能日志时出错: {e}")
    
    def save_logs_on_crash(self):
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            crash_log_file = os.path.join(self.logs_dir, f'crash_log_{timestamp}.txt')
            
            log_content = self.panel.log_text.get(1.0, 'end')
            
            with open(crash_log_file, 'w', encoding='utf-8') as f:
                f.write("服务器崩溃日志\n")
                f.write("=" * 60 + "\n")
                f.write(f"崩溃时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")
                f.write(log_content)
            
            print(f"崩溃日志已保存到: {crash_log_file}")
        except Exception as e:
            print(f"保存崩溃日志时出错: {e}")
    
    def clear_logs(self):
        self.panel.log_text.config(state='normal')
        self.panel.log_text.delete(1.0, 'end')
        self.panel.log_text.config(state='disabled')
    
    def export_logs(self):
        filename = filedialog.asksaveasfilename(
            title="导出日志",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.panel.log_text.get(1.0, 'end'))
                messagebox.showinfo("成功", f"日志已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出日志时出错: {str(e)}")
    
    def search_logs(self):
        search_term = simpledialog.askstring("查找日志", "请输入要查找的内容:", parent=self.panel.root)
        if search_term:
            messagebox.showinfo("查找", f"搜索: {search_term}")
    
    def log_message(self, message):
        self.panel.log_text.config(state='normal')
        self.panel.log_text.insert('end', f"{message}\n")
        self.panel.log_text.see('end')
        self.panel.log_text.config(state='disabled')
        
        if "INFO]" in message or "WARN]" in message or "ERROR]" in message:
            self.panel.info_text.config(state='normal')
            self.panel.info_text.insert('end', f"{message}\n")
            self.panel.info_text.see('end')
            self.panel.info_text.config(state='disabled')
