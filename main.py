import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import json
import os
from datetime import datetime
from pathlib import Path
from backup_manager import BackupManager
from config_manager import ConfigManager

class BackupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Copias de Seguridad")
        self.root.geometry("900x700")
        
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager(self.log_message)
        
        self.setup_ui()
        self.load_profiles()
        
    def setup_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.tab_backup = ttk.Frame(notebook)
        self.tab_schedule = ttk.Frame(notebook)
        self.tab_profiles = ttk.Frame(notebook)
        self.tab_settings = ttk.Frame(notebook)
        
        notebook.add(self.tab_backup, text='Copia de Seguridad')
        notebook.add(self.tab_schedule, text='Programación')
        notebook.add(self.tab_profiles, text='Perfiles')
        notebook.add(self.tab_settings, text='Configuración')
        
        self.setup_backup_tab()
        self.setup_schedule_tab()
        self.setup_profiles_tab()
        self.setup_settings_tab()
        
    def setup_backup_tab(self):
        main_frame = ttk.Frame(self.tab_backup, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        source_frame = ttk.LabelFrame(main_frame, text="Origen", padding="10")
        source_frame.pack(fill='x', pady=5)
        
        ttk.Label(source_frame, text="Carpetas a respaldar:").pack(anchor='w')
        
        source_list_frame = ttk.Frame(source_frame)
        source_list_frame.pack(fill='both', expand=True, pady=5)
        
        self.source_listbox = tk.Listbox(source_list_frame, height=4)
        self.source_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(source_list_frame, orient='vertical', command=self.source_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.source_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(source_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="Agregar Carpeta", command=self.add_source_folder).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Eliminar", command=self.remove_source_folder).pack(side='left', padx=2)
        
        dest_frame = ttk.LabelFrame(main_frame, text="Destino", padding="10")
        dest_frame.pack(fill='x', pady=5)
        
        ttk.Label(dest_frame, text="Tipo de destino:").pack(anchor='w')
        
        self.dest_type = tk.StringVar(value="local")
        ttk.Radiobutton(dest_frame, text="Disco Local/Externo", variable=self.dest_type, 
                       value="local", command=self.update_destination_ui).pack(anchor='w')
        ttk.Radiobutton(dest_frame, text="NAS (Red Local)", variable=self.dest_type, 
                       value="nas", command=self.update_destination_ui).pack(anchor='w')
        ttk.Radiobutton(dest_frame, text="Google Drive", variable=self.dest_type, 
                       value="gdrive", command=self.update_destination_ui).pack(anchor='w')
        ttk.Radiobutton(dest_frame, text="Dropbox", variable=self.dest_type, 
                       value="dropbox", command=self.update_destination_ui).pack(anchor='w')
        
        self.dest_config_frame = ttk.Frame(dest_frame)
        self.dest_config_frame.pack(fill='x', pady=5)
        
        self.update_destination_ui()
        
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill='x', pady=10)
        
        self.backup_btn = ttk.Button(action_frame, text="Iniciar Copia de Seguridad", 
                                     command=self.start_backup, style='Accent.TButton')
        self.backup_btn.pack(side='left', padx=5)
        
        ttk.Button(action_frame, text="Detener", command=self.stop_backup).pack(side='left', padx=5)
        
        progress_frame = ttk.LabelFrame(main_frame, text="Progreso", padding="10")
        progress_frame.pack(fill='both', expand=True, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Listo para iniciar")
        self.status_label.pack(anchor='w')
        
        ttk.Label(progress_frame, text="Registro de actividad:").pack(anchor='w', pady=(10,0))
        
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=10, state='disabled')
        self.log_text.pack(fill='both', expand=True)
        
    def setup_schedule_tab(self):
        main_frame = ttk.Frame(self.tab_schedule, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text="Programar copias de seguridad automáticas", 
                 font=('', 12, 'bold')).pack(anchor='w', pady=10)
        
        self.schedule_enabled = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Activar programación automática", 
                       variable=self.schedule_enabled).pack(anchor='w', pady=5)
        
        freq_frame = ttk.LabelFrame(main_frame, text="Frecuencia", padding="10")
        freq_frame.pack(fill='x', pady=10)
        
        self.frequency = tk.StringVar(value="daily")
        ttk.Radiobutton(freq_frame, text="Diaria", variable=self.frequency, value="daily").pack(anchor='w')
        ttk.Radiobutton(freq_frame, text="Semanal", variable=self.frequency, value="weekly").pack(anchor='w')
        ttk.Radiobutton(freq_frame, text="Mensual", variable=self.frequency, value="monthly").pack(anchor='w')
        
        time_frame = ttk.LabelFrame(main_frame, text="Hora de ejecución", padding="10")
        time_frame.pack(fill='x', pady=10)
        
        time_input_frame = ttk.Frame(time_frame)
        time_input_frame.pack(anchor='w')
        
        ttk.Label(time_input_frame, text="Hora:").pack(side='left', padx=5)
        self.hour_var = tk.StringVar(value="02")
        ttk.Spinbox(time_input_frame, from_=0, to=23, textvariable=self.hour_var, 
                   width=5, format="%02.0f").pack(side='left')
        
        ttk.Label(time_input_frame, text="Minutos:").pack(side='left', padx=5)
        self.minute_var = tk.StringVar(value="00")
        ttk.Spinbox(time_input_frame, from_=0, to=59, textvariable=self.minute_var, 
                   width=5, format="%02.0f").pack(side='left')
        
        ttk.Button(main_frame, text="Guardar Programación", 
                  command=self.save_schedule).pack(pady=20)
        
    def setup_profiles_tab(self):
        main_frame = ttk.Frame(self.tab_profiles, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text="Perfiles de Respaldo", 
                 font=('', 12, 'bold')).pack(anchor='w', pady=10)
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill='both', expand=True, pady=10)
        
        self.profile_listbox = tk.Listbox(list_frame, height=10)
        self.profile_listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.profile_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.profile_listbox.config(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="Nuevo Perfil", command=self.new_profile).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cargar Perfil", command=self.load_profile).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Guardar Perfil", command=self.save_profile).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Eliminar Perfil", command=self.delete_profile).pack(side='left', padx=5)
        
    def setup_settings_tab(self):
        main_frame = ttk.Frame(self.tab_settings, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text="Configuración de APIs", 
                 font=('', 12, 'bold')).pack(anchor='w', pady=10)
        
        gdrive_frame = ttk.LabelFrame(main_frame, text="Google Drive", padding="10")
        gdrive_frame.pack(fill='x', pady=10)
        
        ttk.Label(gdrive_frame, text="Archivo credentials.json:").pack(anchor='w')
        cred_frame = ttk.Frame(gdrive_frame)
        cred_frame.pack(fill='x', pady=5)
        
        self.gdrive_cred_path = tk.StringVar()
        ttk.Entry(cred_frame, textvariable=self.gdrive_cred_path, state='readonly').pack(side='left', fill='x', expand=True)
        ttk.Button(cred_frame, text="Seleccionar", command=self.select_gdrive_credentials).pack(side='left', padx=5)
        
        dropbox_frame = ttk.LabelFrame(main_frame, text="Dropbox", padding="10")
        dropbox_frame.pack(fill='x', pady=10)
        
        ttk.Label(dropbox_frame, text="Access Token:").pack(anchor='w')
        self.dropbox_token = tk.StringVar()
        ttk.Entry(dropbox_frame, textvariable=self.dropbox_token, show='*').pack(fill='x', pady=5)
        
        ttk.Button(main_frame, text="Guardar Configuración", 
                  command=self.save_settings).pack(pady=20)
        
    def update_destination_ui(self):
        for widget in self.dest_config_frame.winfo_children():
            widget.destroy()
            
        dest_type = self.dest_type.get()
        
        if dest_type == "local":
            ttk.Label(self.dest_config_frame, text="Ruta de destino:").pack(anchor='w')
            path_frame = ttk.Frame(self.dest_config_frame)
            path_frame.pack(fill='x', pady=5)
            
            self.local_path = tk.StringVar()
            ttk.Entry(path_frame, textvariable=self.local_path, state='readonly').pack(side='left', fill='x', expand=True)
            ttk.Button(path_frame, text="Seleccionar", command=self.select_local_path).pack(side='left', padx=5)
            
        elif dest_type == "nas":
            ttk.Label(self.dest_config_frame, text="Servidor NAS:").pack(anchor='w')
            self.nas_server = tk.StringVar()
            ttk.Entry(self.dest_config_frame, textvariable=self.nas_server).pack(fill='x', pady=2)
            
            ttk.Label(self.dest_config_frame, text="Carpeta compartida:").pack(anchor='w', pady=(5,0))
            self.nas_share = tk.StringVar()
            ttk.Entry(self.dest_config_frame, textvariable=self.nas_share).pack(fill='x', pady=2)
            
            ttk.Label(self.dest_config_frame, text="Usuario:").pack(anchor='w', pady=(5,0))
            self.nas_user = tk.StringVar()
            ttk.Entry(self.dest_config_frame, textvariable=self.nas_user).pack(fill='x', pady=2)
            
            ttk.Label(self.dest_config_frame, text="Contraseña:").pack(anchor='w', pady=(5,0))
            self.nas_password = tk.StringVar()
            ttk.Entry(self.dest_config_frame, textvariable=self.nas_password, show='*').pack(fill='x', pady=2)
            
        elif dest_type == "gdrive":
            ttk.Label(self.dest_config_frame, text="Carpeta en Google Drive:").pack(anchor='w')
            self.gdrive_folder = tk.StringVar(value="Backups")
            ttk.Entry(self.dest_config_frame, textvariable=self.gdrive_folder).pack(fill='x', pady=5)
            ttk.Label(self.dest_config_frame, text="Configura las credenciales en la pestaña de Configuración", 
                     foreground='blue').pack(anchor='w')
            
        elif dest_type == "dropbox":
            ttk.Label(self.dest_config_frame, text="Carpeta en Dropbox:").pack(anchor='w')
            self.dropbox_folder = tk.StringVar(value="/Backups")
            ttk.Entry(self.dest_config_frame, textvariable=self.dropbox_folder).pack(fill='x', pady=5)
            ttk.Label(self.dest_config_frame, text="Configura el token en la pestaña de Configuración", 
                     foreground='blue').pack(anchor='w')
            
    def add_source_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta para respaldar")
        if folder:
            self.source_listbox.insert(tk.END, folder)
            
    def remove_source_folder(self):
        selection = self.source_listbox.curselection()
        if selection:
            self.source_listbox.delete(selection[0])
            
    def select_local_path(self):
        folder = filedialog.askdirectory(title="Seleccionar destino para copias de seguridad")
        if folder:
            self.local_path.set(folder)
            
    def select_gdrive_credentials(self):
        file = filedialog.askopenfilename(
            title="Seleccionar archivo credentials.json de Google Drive",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file:
            self.gdrive_cred_path.set(file)
            
    def log_message(self, message):
        self.log_text.config(state='normal')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def update_progress(self, value, status=""):
        self.progress_var.set(value)
        if status:
            self.status_label.config(text=status)
            
    def start_backup(self):
        sources = list(self.source_listbox.get(0, tk.END))
        
        if not sources:
            messagebox.showwarning("Advertencia", "Selecciona al menos una carpeta para respaldar")
            return
            
        dest_type = self.dest_type.get()
        dest_config = {}
        
        if dest_type == "local":
            if not hasattr(self, 'local_path') or not self.local_path.get():
                messagebox.showwarning("Advertencia", "Selecciona la ruta de destino")
                return
            dest_config['path'] = self.local_path.get()
            
        elif dest_type == "nas":
            if not all([self.nas_server.get(), self.nas_share.get()]):
                messagebox.showwarning("Advertencia", "Completa la configuración del NAS")
                return
            dest_config.update({
                'server': self.nas_server.get(),
                'share': self.nas_share.get(),
                'username': self.nas_user.get(),
                'password': self.nas_password.get()
            })
            
        elif dest_type == "gdrive":
            config = self.config_manager.load_config()
            if 'gdrive_credentials' not in config:
                messagebox.showwarning("Advertencia", "Configura las credenciales de Google Drive en Configuración")
                return
            dest_config.update({
                'credentials_path': config['gdrive_credentials'],
                'folder_name': self.gdrive_folder.get()
            })
            
        elif dest_type == "dropbox":
            config = self.config_manager.load_config()
            if 'dropbox_token' not in config:
                messagebox.showwarning("Advertencia", "Configura el token de Dropbox en Configuración")
                return
            dest_config.update({
                'token': config['dropbox_token'],
                'folder_path': self.dropbox_folder.get()
            })
            
        self.backup_btn.config(state='disabled')
        self.log_message("Iniciando copia de seguridad...")
        
        def backup_thread():
            try:
                self.backup_manager.backup(sources, dest_type, dest_config, self.update_progress)
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Copia de seguridad completada"))
            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error en la copia de seguridad: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.backup_btn.config(state='normal'))
                
        thread = threading.Thread(target=backup_thread, daemon=True)
        thread.start()
        
    def stop_backup(self):
        self.backup_manager.stop()
        self.log_message("Deteniendo copia de seguridad...")
        
    def save_schedule(self):
        schedule_config = {
            'enabled': self.schedule_enabled.get(),
            'frequency': self.frequency.get(),
            'hour': self.hour_var.get(),
            'minute': self.minute_var.get()
        }
        self.config_manager.save_schedule(schedule_config)
        messagebox.showinfo("Éxito", "Programación guardada correctamente")
        
    def save_settings(self):
        settings = {}
        
        if self.gdrive_cred_path.get():
            settings['gdrive_credentials'] = self.gdrive_cred_path.get()
            
        if self.dropbox_token.get():
            settings['dropbox_token'] = self.dropbox_token.get()
            
        self.config_manager.update_config(settings)
        messagebox.showinfo("Éxito", "Configuración guardada correctamente")
        
    def new_profile(self):
        self.source_listbox.delete(0, tk.END)
        self.log_message("Nuevo perfil creado")
        
    def save_profile(self):
        name = simpledialog.askstring("Guardar Perfil", "Nombre del perfil:")
        if name:
            profile = {
                'sources': list(self.source_listbox.get(0, tk.END)),
                'dest_type': self.dest_type.get()
            }
            self.config_manager.save_profile(name, profile)
            self.load_profiles()
            messagebox.showinfo("Éxito", f"Perfil '{name}' guardado")
            
    def load_profile(self):
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un perfil")
            return
            
        profile_name = self.profile_listbox.get(selection[0])
        profile = self.config_manager.load_profile(profile_name)
        
        if profile:
            self.source_listbox.delete(0, tk.END)
            for source in profile.get('sources', []):
                self.source_listbox.insert(tk.END, source)
            self.dest_type.set(profile.get('dest_type', 'local'))
            self.update_destination_ui()
            self.log_message(f"Perfil '{profile_name}' cargado")
            
    def delete_profile(self):
        selection = self.profile_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un perfil")
            return
            
        profile_name = self.profile_listbox.get(selection[0])
        if messagebox.askyesno("Confirmar", f"¿Eliminar perfil '{profile_name}'?"):
            self.config_manager.delete_profile(profile_name)
            self.load_profiles()
            
    def load_profiles(self):
        self.profile_listbox.delete(0, tk.END)
        profiles = self.config_manager.get_profiles()
        for profile in profiles:
            self.profile_listbox.insert(tk.END, profile)

def main():
    root = tk.Tk()
    app = BackupApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
