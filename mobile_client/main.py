"""
EventHub - Kök Başlatıcı (Root Launcher)
"""
import sys
import os

# Proje dizinini ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import flet as ft
from src.main import main

if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
