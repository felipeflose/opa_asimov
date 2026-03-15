import psutil
import os

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if 'python' in proc.info['name'].lower():
            print(f"PID: {proc.info['pid']} | CMD: {' '.join(proc.info['cmdline'] if proc.info['cmdline'] else [])}")
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
