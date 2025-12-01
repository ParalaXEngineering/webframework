# Future Improvement: Database Abstraction Layer

## Current State

The framework uses JSON files for persistent storage:

```
website/
├── auth/
│   ├── users.json       # User accounts
│   ├── permissions.json # Permission definitions
│   └── groups.json      # User groups
├── config.json          # Application settings
└── file_manager/
    └── metadata.json    # File metadata
```

This works well for:
- Small deployments (< 100 users)
- Single-instance applications
- Embedded systems with limited resources
- Simple backup (just copy the JSON files)

## Limitations of JSON Storage

1. **No concurrent write safety** - Two processes writing = data corruption
2. **Full file rewrite on every save** - Slow for large datasets
3. **No transactions** - Partial writes on crash = inconsistent state
4. **No querying** - Must load entire file to search
5. **No indexing** - O(n) lookups for everything
6. **Memory usage** - Entire dataset must fit in RAM

## When to Consider Database

You might need a database when:
- Multiple workers/processes access data simultaneously
- Dataset grows beyond a few thousand records
- You need complex queries (e.g., "all users who logged in last week")
- Audit trails are required
- Data integrity is critical

## Proposed Solution: Storage Backend Abstraction

### Phase 1: Define Abstract Interface

```python
# src/modules/storage/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar('T')


class StorageBackend(ABC, Generic[T]):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """Get a single item by key."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[T]:
        """Get all items."""
        pass
    
    @abstractmethod
    def save(self, key: str, item: T) -> None:
        """Save an item."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete an item. Returns True if existed."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass
    
    @abstractmethod
    def find(self, **filters) -> List[T]:
        """Find items matching filters."""
        pass
```

### Phase 2: JSON Backend (Current Behavior)

```python
# src/modules/storage/json_backend.py
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from .base import StorageBackend

T = TypeVar('T', bound=Dict[str, Any])


class JSONStorageBackend(StorageBackend[T]):
    """JSON file-based storage backend.
    
    Thread-safe with file locking for single-process deployments.
    """
    
    def __init__(self, file_path: str, key_field: str = 'id'):
        self.file_path = Path(file_path)
        self.key_field = key_field
        self._lock = threading.RLock()
        self._cache: Optional[Dict[str, T]] = None
    
    def _load(self) -> Dict[str, T]:
        """Load data from file with caching."""
        if self._cache is not None:
            return self._cache
        
        if not self.file_path.exists():
            self._cache = {}
            return self._cache
        
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        
        # Convert list to dict keyed by key_field
        if isinstance(data, list):
            self._cache = {item[self.key_field]: item for item in data}
        else:
            self._cache = data
        
        return self._cache
    
    def _save(self) -> None:
        """Persist cache to file."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temp file then rename (atomic on POSIX)
        temp_path = self.file_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self._cache, f, indent=2)
        temp_path.rename(self.file_path)
    
    def get(self, key: str) -> Optional[T]:
        with self._lock:
            return self._load().get(key)
    
    def get_all(self) -> List[T]:
        with self._lock:
            return list(self._load().values())
    
    def save(self, key: str, item: T) -> None:
        with self._lock:
            self._load()[key] = item
            self._save()
    
    def delete(self, key: str) -> bool:
        with self._lock:
            data = self._load()
            if key in data:
                del data[key]
                self._save()
                return True
            return False
    
    def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._load()
    
    def find(self, **filters) -> List[T]:
        with self._lock:
            results = []
            for item in self._load().values():
                match = all(
                    item.get(k) == v 
                    for k, v in filters.items()
                )
                if match:
                    results.append(item)
            return results
    
    def invalidate_cache(self) -> None:
        """Force reload from disk on next access."""
        with self._lock:
            self._cache = None
```

### Phase 3: SQLite Backend (Upgrade Path)

```python
# src/modules/storage/sqlite_backend.py
import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar

from .base import StorageBackend

T = TypeVar('T', bound=Dict[str, Any])


class SQLiteStorageBackend(StorageBackend[T]):
    """SQLite-based storage backend.
    
    Provides ACID transactions, concurrent access, and better performance
    for larger datasets.
    """
    
    def __init__(
        self, 
        db_path: str, 
        table_name: str,
        key_field: str = 'id'
    ):
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.key_field = key_field
        self._local = threading.local()
        self._init_db()
    
    @property
    def _conn(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self) -> None:
        """Create table if not exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn.execute(f'''
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self._conn.commit()
    
    def get(self, key: str) -> Optional[T]:
        cursor = self._conn.execute(
            f'SELECT data FROM {self.table_name} WHERE key = ?',
            (key,)
        )
        row = cursor.fetchone()
        return json.loads(row['data']) if row else None
    
    def get_all(self) -> List[T]:
        cursor = self._conn.execute(
            f'SELECT data FROM {self.table_name}'
        )
        return [json.loads(row['data']) for row in cursor]
    
    def save(self, key: str, item: T) -> None:
        self._conn.execute(f'''
            INSERT OR REPLACE INTO {self.table_name} (key, data, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(item)))
        self._conn.commit()
    
    def delete(self, key: str) -> bool:
        cursor = self._conn.execute(
            f'DELETE FROM {self.table_name} WHERE key = ?',
            (key,)
        )
        self._conn.commit()
        return cursor.rowcount > 0
    
    def exists(self, key: str) -> bool:
        cursor = self._conn.execute(
            f'SELECT 1 FROM {self.table_name} WHERE key = ? LIMIT 1',
            (key,)
        )
        return cursor.fetchone() is not None
    
    def find(self, **filters) -> List[T]:
        # For simple cases, filter in Python
        # For production, build proper SQL WHERE clause
        all_items = self.get_all()
        return [
            item for item in all_items
            if all(item.get(k) == v for k, v in filters.items())
        ]
```

### Phase 4: Refactor AuthManager to Use Backend

```python
# src/modules/auth/auth_manager.py

from ..storage import StorageBackend, JSONStorageBackend

class AuthManager:
    """Authentication manager with pluggable storage backend."""
    
    def __init__(
        self, 
        auth_dir: str,
        backend: Optional[StorageBackend] = None
    ):
        self.auth_dir = auth_dir
        
        # Use provided backend or default to JSON
        if backend:
            self._users = backend
        else:
            self._users = JSONStorageBackend(
                os.path.join(auth_dir, 'users.json'),
                key_field='username'
            )
    
    def get_user(self, username: str) -> Optional[User]:
        data = self._users.get(username)
        return User(**data) if data else None
    
    def save_user(self, user: User) -> None:
        self._users.save(user.username, user.to_dict())
    
    def delete_user(self, username: str) -> bool:
        return self._users.delete(username)
    
    def list_users(self) -> List[User]:
        return [User(**data) for data in self._users.get_all()]
```

### Phase 5: Configuration-Based Backend Selection

```python
# website/config.json
{
    "storage": {
        "backend": "sqlite",  // or "json"
        "sqlite": {
            "path": "website/data/app.db"
        },
        "json": {
            "directory": "website/auth"
        }
    }
}
```

```python
# src/modules/storage/__init__.py

def create_backend(config: dict, table_name: str) -> StorageBackend:
    """Factory function to create storage backend from config."""
    backend_type = config.get('backend', 'json')
    
    if backend_type == 'sqlite':
        from .sqlite_backend import SQLiteStorageBackend
        return SQLiteStorageBackend(
            db_path=config['sqlite']['path'],
            table_name=table_name
        )
    else:
        from .json_backend import JSONStorageBackend
        return JSONStorageBackend(
            file_path=os.path.join(config['json']['directory'], f'{table_name}.json')
        )
```

## Migration Path

### From JSON to SQLite

```python
# scripts/migrate_to_sqlite.py
from src.modules.storage import JSONStorageBackend, SQLiteStorageBackend

def migrate(json_path: str, sqlite_path: str, table_name: str):
    """Migrate data from JSON to SQLite."""
    json_backend = JSONStorageBackend(json_path)
    sqlite_backend = SQLiteStorageBackend(sqlite_path, table_name)
    
    for item in json_backend.get_all():
        key = item.get('id') or item.get('username') or item.get('name')
        sqlite_backend.save(key, item)
    
    print(f"Migrated {len(json_backend.get_all())} items to SQLite")

if __name__ == '__main__':
    migrate('website/auth/users.json', 'website/data/app.db', 'users')
    migrate('website/auth/groups.json', 'website/data/app.db', 'groups')
    migrate('website/auth/permissions.json', 'website/data/app.db', 'permissions')
```

## Benefits

1. **No code changes for existing deployments** - JSON backend works exactly as before
2. **Easy upgrade path** - Change config, run migration script
3. **Testability** - Can use in-memory backend for tests
4. **Future-proof** - Can add PostgreSQL, Redis, etc. backends later

## Files to Create

- [ ] `src/modules/storage/__init__.py`
- [ ] `src/modules/storage/base.py`
- [ ] `src/modules/storage/json_backend.py`
- [ ] `src/modules/storage/sqlite_backend.py`
- [ ] `scripts/migrate_to_sqlite.py`

## Files to Modify

- [ ] `src/modules/auth/auth_manager.py` - Use storage backend
- [ ] `src/modules/settings/manager.py` - Use storage backend
- [ ] `src/modules/file_manager/` - Use storage backend for metadata

## Estimated Effort

- Define interfaces: 1 hour
- JSON backend: 2 hours
- SQLite backend: 2 hours
- Refactor AuthManager: 2 hours
- Refactor SettingsManager: 1 hour
- Migration script: 1 hour
- Testing: 3 hours

**Total: ~12 hours**

## When to Implement

**Not urgent** - Current JSON storage works fine for intended use case.

Consider implementing when:
- You need multiple worker processes
- User count exceeds ~500
- You need audit logs or data history
- Performance becomes an issue

## Alternative: SQLite for Session Storage Only

A smaller change: just use SQLite for Flask sessions instead of filesystem.

```python
# In setup_app()
app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SESSION_SQLALCHEMY_TABLE"] = "sessions"

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)
```

This solves the session file explosion without touching auth/settings storage.
