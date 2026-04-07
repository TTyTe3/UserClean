import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
import sys
import time

class SchoolPCCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("UserCleaner v1.0.2")
        self.root.geometry("850x700")
        self.root.minsize(800, 650)
        self.root.resizable(True, True)
        self.protected_users = ['учитель', 'ученик', 'admin', 'всош', 'olymp', 'user', 'alext','all users','все пользователи',"Робокласс"]     
        self.cleanup_threshold = 0.75 * 1024**3  
        self.scan_results = {}
        self.setup_ui()
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        title = ttk.Label(main_frame, text="Userfolders cleaner", font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=2, pady=5)
        protect_frame = ttk.LabelFrame(main_frame, text="Protected users", padding="5")
        protect_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        protect_text = ', '.join(self.protected_users)
        ttk.Label(protect_frame, text=f"Dont touched: {protect_text}", font=('Arial', 9, 'bold')).pack()
        settings_frame = ttk.LabelFrame(main_frame, text="Clean settings", padding="5")
        settings_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)        
        ttk.Label(settings_frame, text="Min for clean:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.threshold_var = tk.StringVar(value="0.75")
        threshold_entry = ttk.Entry(settings_frame, textvariable=self.threshold_var, width=10)
        threshold_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(settings_frame, text="ГБ").grid(row=0, column=2, sticky=tk.W)
        ttk.Label(settings_frame, text="(All data of users with bigger size will be deleted)", font=('Arial', 8)).grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=2)   
        update_btn = ttk.Button(settings_frame, text="Save", command=self.update_threshold, width=10)
        update_btn.grid(row=0, column=3, padx=10)
        quick_frame = ttk.LabelFrame(main_frame, text="Fast clean", padding="10")
        quick_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(quick_frame, text="Deletes everything from downloads and temp files\nfrom ALL unprotected users").pack()
        self.quick_btn = ttk.Button(quick_frame, text="Start fast clean", command=self.quick_clean, width=30)
        self.quick_btn.pack(pady=5)
        full_frame = ttk.LabelFrame(main_frame, text="Full clean", padding="10")
        full_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(full_frame, text=f"Found users with folders bigger than {self.threshold_var.get()} GB and deletes it").pack()
        self.scan_btn = ttk.Button(full_frame, text="Scan all", command=self.start_full_scan, width=30)
        self.scan_btn.pack(pady=5)
        self.clean_btn = ttk.Button(full_frame, text="DELETE FOUND", command=self.confirm_cleanup, width=30, state='disabled')
        self.clean_btn.pack(pady=5)
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        log_frame = ttk.LabelFrame(main_frame, text="Operations log", padding="5")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, width=90, font=('Courier', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
    def update_threshold(self):
        try:
            new_threshold = float(self.threshold_var.get())
            if new_threshold > 0:
                self.cleanup_threshold = new_threshold * 1024**3
                self.log(f"New deleting min: {new_threshold} ГБ")
                for child in self.root.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for frame in child.winfo_children():
                            if isinstance(frame, ttk.LabelFrame) and frame.winfo_name() == '!labelframe4':
                                for label in frame.winfo_children():
                                    if isinstance(label, ttk.Label) and label.winfo_class() == 'TLabel':
                                        if label.cget('text').startswith('Founding users'):
                                            label.config(text=f"finding users with folder size bigger than {self.threshold_var.get()} GB and COMPLETELY deletes folders")
            else:
                messagebox.showwarning("Error", "Min value must be bigger than zero")
        except ValueError:
            messagebox.showwarning("Error", "Enter a correct number")
    def is_protected(self, username):
        return username.lower() in self.protected_users
        
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    def get_user_folder_size(self, username):
        user_path = Path(f"C:/Users/{username}")
        if not user_path.exists():
            return 0
        total_size = 0
        try:
            for item in user_path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (PermissionError, OSError):
                        continue
        except (PermissionError, OSError):
            pass
        return total_size
    def format_size(self, size_bytes):
        if size_bytes == 0:
            return "0 Б"
        size_names = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    def delete_folder_contents(self, folder_path):
        deleted_count = 0
        deleted_size = 0
        try:
            for item in folder_path.iterdir():
                try:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        deleted_size += size
                    elif item.is_dir():
                        size = self.get_folder_size(item)
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1
                        deleted_size += size
                except Exception:
                    continue
        except Exception:
            pass
        return deleted_count, deleted_size
    def get_folder_size(self, folder_path):
        total = 0
        try:
            for item in folder_path.rglob('*'):
                if item.is_file():
                    try:
                        total += item.stat().st_size
                    except:
                        continue
        except:
            pass
        return total
    def delete_user_folder(self, username):
        user_path = Path(f"C:/Users/{username}")
        if not user_path.exists():
            return 0, 0
        size = self.get_user_folder_size(username)      
        try:
            for item in user_path.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                except Exception as e:
                    self.log(f"  Error during deletion {item.name}: {e}")
            user_path.mkdir(exist_ok=True)
            for folder in ['Desktop','Downloads']:
                (user_path / folder).mkdir(exist_ok=True)
            return 1, size
        except Exception as e:
            self.log(f"  CRITICAL ERROR WHILE DELETING {username}: {e}")
            return 0, 0
    def quick_clean(self):
        if not messagebox.askyesno("Warning", "Fast cleaning will delete ALL in this folders:\n" + "Downloads, Desktop\n\n""from ALL unprotected users\n\n""Are you sure?"):
            return
        self.quick_btn.config(state='disabled')
        self.progress.start()
        self.log("=" * 70)
        self.log("Fast cleaning started")
        def clean_thread():
            users_path = Path("C:/Users")
            if not users_path.exists():
                self.log("CRITICAL ERROR: C:/Users NOT FOUND")
                self.root.after(0, self.finish_operation)
                return
            users = [u.name for u in users_path.iterdir() if u.is_dir() and not u.name.startswith('.')]
            total_deleted = 0
            total_size = 0
            for username in users:
                if self.is_protected(username):
                    self.log(f"\nSkipped protected user: {username}")
                    continue
                self.log(f"\nWatching user: {username}")
                user_path = Path(f"C:/Users/{username}")
                user_deleted = 0
                user_size = 0
                folders_to_clean = ['Downloads','Desktop', 'AppData/Local/Temp']
                for folder_name in folders_to_clean:
                    folder_path = user_path / folder_name
                    if folder_path.exists():
                        self.log(f"  Cleaning: {folder_path}")
                        try:
                            deleted_count, deleted_size = self.delete_folder_contents(folder_path)
                            if deleted_count > 0:
                                user_deleted += deleted_count
                                user_size += deleted_size
                                self.log(f"    Deleted: {deleted_count} objects ({self.format_size(deleted_size)})")
                        except Exception as e:
                            self.log(f"    ERROR: {e}")
                if user_deleted > 0:
                    total_deleted += user_deleted
                    total_size += user_size
                    self.log(f"  {username}: deleted {self.format_size(user_size)}")
            self.log("\n" + "=" * 70)
            self.log(f"Fast cleaning completed")
            self.log(f"Objects deleted: {total_deleted}")
            self.log(f"Size cleaned: {self.format_size(total_size)}")  
            self.root.after(0, self.finish_operation)
        threading.Thread(target=clean_thread, daemon=True).start()
    def full_scan(self):
        users_path = Path("C:/Users")
        if not users_path.exists():
            self.log("CRITICAL ERROR C:/Users NOT FOUND")
            return False
        self.scan_results = {}
        users = [u.name for u in users_path.iterdir() if u.is_dir() and not u.name.startswith('.')]
        self.log("=" * 70)
        self.log("Starting full cleaning")
        self.log(f"Found users: {len(users)}")
        self.log(f"Delete min: {self.cleanup_threshold / (1024**3):.2f} ГБ")
        for username in users:
            if self.is_protected(username):
                self.log(f"\nSkipped protected  {username}")
                continue
            self.log(f"\nScanning: {username}")
            self.log(f"  Calculation...")
            size = self.get_user_folder_size(username)
            size_gb = size / (1024**3)
            
            if size >= self.cleanup_threshold:
                self.scan_results[username] = size
                if size_gb > 15:
                    self.log(f"  SIZE: {self.format_size(size)} (>15 GB) Found - for delete")
                else:
                    self.log(f"  SIZE: {self.format_size(size)} - FOR DELETE")
            else:
                self.log(f"  SIZE: {self.format_size(size)} - GOOD")
        
        self.log("\n" + "=" * 70)
        self.log("Scan results:")
        if self.scan_results:
            total_size = 0
            for username, size in self.scan_results.items():
                size_gb = size / (1024**3)
                total_size += size
                if size_gb > 15:
                    self.log(f"  {username}: {self.format_size(size)} (>15 GB) For DELETE")
                else:
                    self.log(f"  {username}: {self.format_size(size)} - FOR DELETE")
            
            total_gb = total_size / (1024**3)
            self.log(f"\nTotal deleting size: {total_gb:.1f} ГБ")
            self.log(f"After cleaning {len(self.scan_results)} users will be deleted")
            return True
        else:
            self.log("  All is good")
            return False
    def start_full_scan(self):
        self.scan_btn.config(state='disabled')
        self.clean_btn.config(state='disabled')
        self.progress.start()
        self.log_text.delete(1.0, tk.END)
        def scan_thread():
            has_garbage = self.full_scan()
            self.root.after(0, lambda: self.scan_complete(has_garbage))
        threading.Thread(target=scan_thread, daemon=True).start()  
    def scan_complete(self, has_garbage):
        self.progress.stop()
        self.scan_btn.config(state='normal')
        if has_garbage:
            self.clean_btn.config(state='normal')
            self.log("\nATTENTION! FULL DELETION OF BAD USERS")
            self.log("Press button to continue")
        else:
            self.log("\nAll is good!")
    def confirm_cleanup(self):
        if not self.scan_results:
            self.log("You don't have data for cleaning.")
            return
        total_gb = sum(self.scan_results.values()) / (1024**3)
        users_list = "\n".join([f"  - {user}: {self.format_size(size)}" 
                                for user, size in self.scan_results.items()])
        message = (f"ATTENTION! FULL DELETION OF USERS:\n\n"
                  f"WILL BE FULL DELETED: {total_gb:.1f} ГБ\n\n"
                  f"Users:\n{users_list}\n\n"
                  f"Data will be full deleted\n\n"
                  f"Are you sure?")
        if messagebox.askyesno("FInal warning", message, icon='warning'):
            self.perform_full_cleanup()
    def perform_full_cleanup(self):
        self.scan_btn.config(state='disabled')
        self.clean_btn.config(state='disabled')
        self.progress.start()
        def cleanup_thread():
            total_deleted = 0
            total_size = 0
            failed = []
            self.log("\n" + "=" * 70)
            self.log("STARTING FULL CLEANING")
            self.log("ATTENTION:SOME USERS WILL BE FULL DELETED")
            for username, size in self.scan_results.items():
                self.log(f"\nDELETING USER: {username}")
                self.log(f"  Size: {self.format_size(size)}")
                deleted, deleted_size = self.delete_user_folder(username)
                if deleted:
                    total_deleted += deleted
                    total_size += deleted_size
                    size_gb = deleted_size / (1024**3)
                    if size_gb > 15:
                        self.log(f"   Deleted: {self.format_size(deleted_size)} (>15 ГБ)")
                    else:
                        self.log(f"   Deleted: {self.format_size(deleted_size)}")
                    self.log(f"  Cleared")
                else:
                    failed.append(username)
                    self.log(f"   ERROR A1")
            self.log("\n" + "=" * 70)
            self.log("Cleaning completed")
            self.log(f"Cleared users: {total_deleted}")
            self.log(f"Cleared: {self.format_size(total_size)}")
            if failed:
                self.log(f"\nError: {', '.join(failed)}")
            self.scan_results = {}
            self.root.after(0, self.finish_operation)    
        threading.Thread(target=cleanup_thread, daemon=True).start()    
    def finish_operation(self):
        self.progress.stop()
        self.scan_btn.config(state='normal')
        self.clean_btn.config(state='disabled')
        self.log("\nGood!")
def main():
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            messagebox.showwarning("Attention", 
                                  "Рекомендуется запускать программу от имени администратора\n"
                                  "для доступа ко всем пользователям.")
    except:
        pass
    root = tk.Tk()
    app = SchoolPCCleaner(root)
    root.mainloop()
if __name__ == "__main__":
    main()