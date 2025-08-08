from admin.manage_modules.content_db import UserOperation
from datetime import datetime


def run_cleanup():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running cleanup task...")
    
    try:
        user_op = UserOperation()
        deleted_count = user_op.delete_expired_content()
        
        if deleted_count > 0:
            print(f"Cleanup successful. Deleted {deleted_count} expired content item(s).")
        else:
            print("No expired content to delete.")
            
    except Exception as e:
        print(f"An error occurred during cleanup: {e}")

if __name__ == "__main__":
    run_cleanup()