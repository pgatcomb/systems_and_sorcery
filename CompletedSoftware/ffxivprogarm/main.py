#!/usr/bin/env python3
"""
FFXIV Market Profit Analyzer
Main entry point for the application
"""
import sys
from gui.main_window import MainWindow

def main():
    """Launch the application"""
    try:
        app = MainWindow()
        app.run()
    except KeyboardInterrupt:
        print("\n[Info] Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"[Error] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
