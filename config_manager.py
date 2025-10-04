import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="backup_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
            
    def update_config(self, updates):
        self.config.update(updates)
        self.save_config()
        
    def save_schedule(self, schedule_config):
        self.config['schedule'] = schedule_config
        self.save_config()
        
    def get_schedule(self):
        return self.config.get('schedule', {})
        
    def save_profile(self, name, profile_data):
        if 'profiles' not in self.config:
            self.config['profiles'] = {}
        self.config['profiles'][name] = profile_data
        self.save_config()
        
    def load_profile(self, name):
        return self.config.get('profiles', {}).get(name)
        
    def get_profiles(self):
        return list(self.config.get('profiles', {}).keys())
        
    def delete_profile(self, name):
        if 'profiles' in self.config and name in self.config['profiles']:
            del self.config['profiles'][name]
            self.save_config()
