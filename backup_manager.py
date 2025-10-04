import os
import shutil
from pathlib import Path
from datetime import datetime
import threading

class BackupManager:
    def __init__(self, log_callback):
        self.log = log_callback
        self.stop_flag = False
        
    def stop(self):
        self.stop_flag = True
        
    def backup(self, sources, dest_type, dest_config, progress_callback):
        self.stop_flag = False
        
        if dest_type == "local":
            self._backup_to_local(sources, dest_config['path'], progress_callback)
        elif dest_type == "nas":
            self._backup_to_nas(sources, dest_config, progress_callback)
        elif dest_type == "gdrive":
            self._backup_to_gdrive(sources, dest_config, progress_callback)
        elif dest_type == "dropbox":
            self._backup_to_dropbox(sources, dest_config, progress_callback)
            
    def _backup_to_local(self, sources, dest_path, progress_callback):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_folder = Path(dest_path) / f"backup_{timestamp}"
        backup_folder.mkdir(parents=True, exist_ok=True)
        
        self.log(f"Creando copia de seguridad en: {backup_folder}")
        
        total_files = sum(1 for source in sources for _ in Path(source).rglob('*') if Path(source).is_dir() or 1)
        processed = 0
        
        for source in sources:
            if self.stop_flag:
                self.log("Copia de seguridad detenida por el usuario")
                return
                
            source_path = Path(source)
            
            if source_path.is_file():
                dest_file = backup_folder / source_path.name
                shutil.copy2(source_path, dest_file)
                self.log(f"Copiado: {source_path.name}")
                processed += 1
                progress_callback(int((processed / max(total_files, 1)) * 100))
            elif source_path.is_dir():
                folder_name = source_path.name
                dest_folder = backup_folder / folder_name
                
                for root, dirs, files in os.walk(source_path):
                    if self.stop_flag:
                        return
                        
                    rel_path = Path(root).relative_to(source_path)
                    current_dest = dest_folder / rel_path
                    current_dest.mkdir(parents=True, exist_ok=True)
                    
                    for file in files:
                        if self.stop_flag:
                            return
                            
                        src_file = Path(root) / file
                        dst_file = current_dest / file
                        
                        try:
                            shutil.copy2(src_file, dst_file)
                            processed += 1
                            if processed % 10 == 0:
                                progress_callback(int((processed / max(total_files, 1)) * 100))
                                self.log(f"Progreso: {processed} archivos copiados")
                        except Exception as e:
                            self.log(f"Error copiando {src_file}: {str(e)}")
                            
        progress_callback(100, "Copia de seguridad completada")
        self.log(f"Copia de seguridad completada: {processed} archivos respaldados")
        
    def _backup_to_nas(self, sources, config, progress_callback):
        from smbclient import register_session, open_file, mkdir
        from smbclient.shutil import copy2
        
        server = config['server']
        share = config['share']
        username = config.get('username', 'guest')
        password = config.get('password', '')
        
        try:
            register_session(server, username=username, password=password)
        except Exception as e:
            self.log(f"Error conectando al NAS: {str(e)}")
            raise Exception(f"No se pudo conectar al NAS {server}. Verifica el servidor, usuario y contraseña.")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nas_path = f"\\\\{server}\\{share}\\backup_{timestamp}"
        
        self.log(f"Conectando a NAS: {server}\\{share}")
        self.log(f"Creando carpeta de respaldo: {nas_path}")
        
        try:
            mkdir(nas_path)
        except Exception as e:
            self.log(f"Error creando carpeta base en NAS: {str(e)}")
            raise Exception(f"No se pudo crear la carpeta de respaldo en el NAS. Verifica los permisos.")
        
        total_files = sum(1 for source in sources for _ in Path(source).rglob('*') if Path(source).is_dir() or 1)
        processed = 0
        
        for source in sources:
            if self.stop_flag:
                self.log("Copia de seguridad detenida")
                return
                
            source_path = Path(source)
            dest_name = source_path.name
            dest_path = f"{nas_path}\\{dest_name}"
            
            self.log(f"Copiando {source} a {dest_path}")
            
            try:
                if source_path.is_file():
                    try:
                        mkdir(nas_path)
                    except:
                        pass
                    copy2(str(source_path), dest_path)
                    processed += 1
                    progress_callback(int((processed / max(total_files, 1)) * 100))
                elif source_path.is_dir():
                    for root, dirs, files in os.walk(source_path):
                        if self.stop_flag:
                            return
                            
                        rel_path = Path(root).relative_to(source_path.parent)
                        current_dest = f"{nas_path}\\{rel_path}".replace('/', '\\')
                        
                        try:
                            mkdir(current_dest)
                        except Exception as e:
                            if "STATUS_OBJECT_NAME_COLLISION" not in str(e):
                                self.log(f"Advertencia creando directorio {current_dest}: {str(e)}")
                        
                        for file in files:
                            if self.stop_flag:
                                return
                                
                            src_file = Path(root) / file
                            dst_file = f"{current_dest}\\{file}"
                            
                            try:
                                copy2(str(src_file), dst_file)
                                processed += 1
                                if processed % 10 == 0:
                                    progress_callback(int((processed / max(total_files, 1)) * 100))
                                    self.log(f"Progreso: {processed} archivos copiados")
                            except Exception as e:
                                self.log(f"Error copiando {file}: {str(e)}")
                                
            except Exception as e:
                self.log(f"Error en copia a NAS: {str(e)}")
                raise
                
        progress_callback(100, "Copia de seguridad en NAS completada")
        self.log(f"Respaldo en NAS completado: {processed} archivos")
        
    def _backup_to_gdrive(self, sources, config, progress_callback):
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        creds = None
        token_file = 'token.pickle'
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    config['credentials_path'], SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
                
        service = build('drive', 'v3', credentials=creds)
        
        folder_name = f"{config['folder_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        folder_id = folder.get('id')
        
        self.log(f"Carpeta creada en Google Drive: {folder_name}")
        
        total_files = sum(1 for source in sources for _ in Path(source).rglob('*') if _.is_file())
        processed = 0
        
        def upload_folder(local_path, parent_id):
            nonlocal processed
            
            for item in Path(local_path).iterdir():
                if self.stop_flag:
                    return
                    
                if item.is_file():
                    file_metadata = {
                        'name': item.name,
                        'parents': [parent_id]
                    }
                    
                    media = MediaFileUpload(str(item), resumable=True)
                    
                    try:
                        service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields='id'
                        ).execute()
                        
                        processed += 1
                        if processed % 5 == 0:
                            progress_callback(int((processed / max(total_files, 1)) * 100))
                            self.log(f"Subidos {processed}/{total_files} archivos")
                    except Exception as e:
                        self.log(f"Error subiendo {item.name}: {str(e)}")
                        
                elif item.is_dir():
                    subfolder_metadata = {
                        'name': item.name,
                        'mimeType': 'application/vnd.google-apps.folder',
                        'parents': [parent_id]
                    }
                    subfolder = service.files().create(body=subfolder_metadata, fields='id').execute()
                    upload_folder(item, subfolder.get('id'))
                    
        for source in sources:
            if self.stop_flag:
                break
            upload_folder(source, folder_id)
            
        progress_callback(100, "Copia en Google Drive completada")
        self.log(f"Respaldo en Google Drive completado: {processed} archivos")
        
    def _backup_to_dropbox(self, sources, config, progress_callback):
        import dropbox
        from dropbox.files import WriteMode
        
        dbx = dropbox.Dropbox(config['token'])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_path = f"{config['folder_path']}/backup_{timestamp}"
        
        self.log(f"Iniciando respaldo en Dropbox: {base_path}")
        
        total_files = sum(1 for source in sources for _ in Path(source).rglob('*') if _.is_file())
        processed = 0
        
        def upload_folder(local_path, dropbox_path):
            nonlocal processed
            
            for item in Path(local_path).iterdir():
                if self.stop_flag:
                    return
                    
                item_dropbox_path = f"{dropbox_path}/{item.name}"
                
                if item.is_file():
                    try:
                        with open(item, 'rb') as f:
                            dbx.files_upload(
                                f.read(),
                                item_dropbox_path,
                                mode=WriteMode('overwrite')
                            )
                        
                        processed += 1
                        if processed % 5 == 0:
                            progress_callback(int((processed / max(total_files, 1)) * 100))
                            self.log(f"Subidos {processed}/{total_files} archivos")
                    except Exception as e:
                        self.log(f"Error subiendo {item.name}: {str(e)}")
                        
                elif item.is_dir():
                    try:
                        dbx.files_create_folder_v2(item_dropbox_path)
                    except:
                        pass
                    upload_folder(item, item_dropbox_path)
                    
        for source in sources:
            if self.stop_flag:
                break
                
            source_path = Path(source)
            dest_path = f"{base_path}/{source_path.name}"
            
            if source_path.is_file():
                with open(source_path, 'rb') as f:
                    dbx.files_upload(f.read(), dest_path, mode=WriteMode('overwrite'))
                processed += 1
            elif source_path.is_dir():
                try:
                    dbx.files_create_folder_v2(dest_path)
                except:
                    pass
                upload_folder(source_path, dest_path)
                
        progress_callback(100, "Copia en Dropbox completada")
        self.log(f"Respaldo en Dropbox completado: {processed} archivos")
