# Shared SQLite Setup Guide

## Option 1: Network Drive/NAS
1. Place `rescuetime.db` on a shared network drive
2. Update `DB_FILE` path in `database.py`:
   ```python
   DB_FILE = "/path/to/shared/drive/rescuetime.db"
   # or on Windows: "\\server\share\rescuetime.db"
   ```

## Option 2: Cloud Storage (Dropbox/OneDrive/Google Drive)
1. Move `rescuetime.db` to your cloud storage folder
2. Update path to point to synced folder:
   ```python
   DB_FILE = "/Users/yourname/Dropbox/rescuetime/rescuetime.db"
   ```

## Important Considerations:
- **Concurrent Access Risk**: Only use from one computer at a time
- **Add File Locking**: Consider implementing application-level locks
- **Backup Strategy**: Cloud storage provides automatic backups
- **Network Issues**: Application may fail if network is down

## File Locking Implementation:
```python
import fcntl  # Unix/Mac
import msvcrt  # Windows

def get_db_connection_with_lock():
    lock_file = f"{DB_FILE}.lock"
    try:
        lock = open(lock_file, 'w')
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return get_db_connection()
    except IOError:
        raise Exception("Database is locked by another instance")
```
