import schedule
import time
import threading
from config_manager import ConfigManager

class BackupScheduler:
    def __init__(self, backup_function):
        self.backup_function = backup_function
        self.config_manager = ConfigManager()
        self.running = False
        self.thread = None
        
    def setup_schedule(self):
        schedule.clear()
        
        schedule_config = self.config_manager.get_schedule()
        
        if not schedule_config.get('enabled', False):
            return
            
        frequency = schedule_config.get('frequency', 'daily')
        hour = schedule_config.get('hour', '02')
        minute = schedule_config.get('minute', '00')
        time_str = f"{hour}:{minute}"
        
        if frequency == 'daily':
            schedule.every().day.at(time_str).do(self.backup_function)
        elif frequency == 'weekly':
            schedule.every().monday.at(time_str).do(self.backup_function)
        elif frequency == 'monthly':
            schedule.every().day.at(time_str).do(self._check_monthly)
            
    def _check_monthly(self):
        import datetime
        if datetime.datetime.now().day == 1:
            self.backup_function()
            
    def start(self):
        self.setup_schedule()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
            
    def _run(self):
        while self.running:
            schedule.run_pending()
            time.sleep(60)
