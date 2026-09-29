"""
GuardianFi AI — Background Automated Excel Synchronization Watcher
Continuously monitors local database state and audit logs, automatically saving
and keeping all 4 Excel workbooks synchronized in the project folders.
"""

import os
import sys
import time
import datetime
from sync_excel import sync_all_spreadsheets, DATA_DIR, DB_FILE, HISTORY_FILE, EXCEL_FILES

def watch_and_sync(poll_interval=5):
    print("=" * 65)
    print("   GUARDIANFI AUTOMATED EXCEL SYNCHRONIZATION WATCHER")
    print("=" * 65)
    print(f"Monitoring:")
    print(f"  • DB File:      {DB_FILE}")
    print(f"  • History File: {HISTORY_FILE}")
    print(f"  • Target Excel Spreadsheets:")
    for key, name in EXCEL_FILES.items():
        print(f"     - {name}")
    print(f"Poll Interval: {poll_interval}s")
    print("Press Ctrl+C to terminate.")
    print("-" * 65)

    last_db_mtime = 0
    last_hist_mtime = 0

    # Initial sync on startup
    try:
        print("[AutoExcelSync] Performing initial synchronization...")
        res = sync_all_spreadsheets()
        print(f"[AutoExcelSync] \u2713 Initial sync successful at {res.get('timestamp')}")
    except Exception as e:
        print(f"[AutoExcelSync Error] Initial sync failed: {e}", file=sys.stderr)

    while True:
        try:
            db_mtime = os.path.getmtime(DB_FILE) if os.path.exists(DB_FILE) else 0
            hist_mtime = os.path.getmtime(HISTORY_FILE) if os.path.exists(HISTORY_FILE) else 0

            needs_sync = False
            if db_mtime > last_db_mtime:
                last_db_mtime = db_mtime
                needs_sync = True
            if hist_mtime > last_hist_mtime:
                last_hist_mtime = hist_mtime
                needs_sync = True

            if needs_sync:
                res = sync_all_spreadsheets()
                now_str = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{now_str}] \u2713 Auto-saved 4 Excel spreadsheets to folder (User data base.xlsx + Ledgers)")

            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n[AutoExcelSync] Watcher stopped.")
            break
        except Exception as e:
            print(f"[AutoExcelSync Error] {e}", file=sys.stderr)
            time.sleep(poll_interval)

if __name__ == '__main__':
    interval = 5
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        interval = int(sys.argv[1])
    if '--once' in sys.argv:
        res = sync_all_spreadsheets()
        print(f"Synchronized 4 Excel files: {list(res['spreadsheets'].keys())}")
    else:
        watch_and_sync(interval)
