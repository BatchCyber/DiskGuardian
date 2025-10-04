import platform

print("=" * 60)
print("SISTEMA DE COPIAS DE SEGURIDAD")
print("=" * 60)
print()
print("Esta aplicación de escritorio está diseñada para Windows")
print("con interfaz gráfica completa usando tkinter.")
print()
print("CARACTERÍSTICAS:")
print("  ✓ Copia de seguridad hacia discos locales/externos")
print("  ✓ Copia de seguridad hacia NAS (red local)")
print("  ✓ Copia de seguridad hacia Google Drive")
print("  ✓ Copia de seguridad hacia Dropbox")
print("  ✓ Programación de copias automáticas")
print("  ✓ Gestión de perfiles de respaldo")
print("  ✓ Interfaz gráfica intuitiva")
print()
print("PARA EJECUTAR EN WINDOWS:")
print("  1. Descarga todos los archivos del proyecto")
print("  2. Asegúrate de tener Python 3.11+ instalado")
print("  3. Instala las dependencias:")
print("     pip install google-api-python-client google-auth-httplib2")
print("     pip install google-auth-oauthlib dropbox smbprotocol schedule")
print("  4. Ejecuta: python main.py")
print()
print("CONFIGURACIÓN:")
print("  • Google Drive: Necesitas credentials.json de Google Cloud")
print("  • Dropbox: Necesitas un Access Token de tu app")
print("  • NAS: Configuración de servidor/carpeta/usuario/contraseña")
print()
print("Sistema actual:", platform.system())
if platform.system() != "Windows":
    print("⚠ Nota: La interfaz gráfica requiere un entorno de escritorio")
print()
print("=" * 60)
print()

print("Verificando módulos instalados...")
modules_ok = True

try:
    from backup_manager import BackupManager
    from config_manager import ConfigManager
    from scheduler import BackupScheduler
    import tkinter
    import dropbox
    import schedule
    import smbprotocol
    from google.oauth2 import credentials
    print("✓ Todos los módulos están correctamente instalados")
except ImportError as e:
    print(f"✗ Error: Falta un módulo - {e}")
    modules_ok = False

if modules_ok:
    print("✓ La aplicación está lista para usarse en Windows")
    print()
    print("Archivos principales:")
    print("  • main.py - Aplicación principal con interfaz gráfica")
    print("  • backup_manager.py - Gestor de copias de seguridad")
    print("  • config_manager.py - Gestión de configuración")
    print("  • scheduler.py - Programación de tareas")
