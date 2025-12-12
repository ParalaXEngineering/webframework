# Main.py Refactoring Plan - Two-Step Approach

## Status: Step 1 COMPLETED ✅

### Step 1: Migrate to AppContext Pattern ✅ COMPLETED
**Goal**: Centralize all framework state in `app_context` singleton

**Completion Date**: December 12, 2025

**Changes Implemented**:
1. ✅ Removed module-level globals from:
   - `src/modules/auth/__init__.py` → `auth_manager` (removed, use `app_context.auth_manager`)
   - `src/modules/settings/__init__.py` → `settings_manager` (removed, use `app_context.settings_manager`)
   - `src/modules/scheduler/__init__.py` → `scheduler_obj`, `scheduler_ltobj` (removed, use `app_context.scheduler`, `app_context.scheduler_lt`)
   - `src/modules/threaded/threaded_manager.py` → `thread_manager_obj` (removed, use `app_context.thread_manager`)
   - `src/modules/site_conf.py` → `site_conf_obj`, `site_conf_app_path` (removed, use `app_context.site_conf`, `app_context.app_path`)

2. ✅ Updated `main.py` to populate `app_context` instead of module globals
   - All manager initialization now sets `app_context` properties
   - Clean initialization flow in `setup_app()`

3. ✅ Updated all consumers to read from `app_context`:
   - All `src/pages/*.py` files (10 files: admin, bug_tracker, common, file_handler, file_manager_admin, logging, packager, settings, threads, updater, user)
   - `src/modules/displayer/displayer.py`
   - `src/modules/threaded/threaded_action.py`
   - `src/modules/threaded/thread_emitter.py`
   - `src/modules/scheduler/scheduler.py`
   - `src/modules/i18n/__init__.py`
   - `src/modules/workflow.py`
   - `src/modules/auth/__init__.py` (decorators)
   - `Manual_Webapp/main.py`
   - `Manual_Webapp/demo_support/*.py` (2 files)

4. ✅ Updated all tests:
   - `tests/unit/test_feature_flags.py`
   - `tests/unit/test_threading.py`
   - `tests/unit/test_workflow.py`
   - `tests/integration/test_conditional_blueprints.py`

**Testing Results**:
- ✅ All unit tests pass (86 tests: 36 threading + 7 feature flags + 43 workflow)
- ✅ All integration tests pass (3 conditional blueprint tests)
- ✅ All frontend tests pass (avatar upload test)
- ✅ Server starts without errors
- ✅ Manual testing: file manager, authorization, user profile all working

**Outcome**: 
- ✅ Clean singleton pattern established
- ✅ No circular imports
- ✅ All 40+ files migrated successfully
- ✅ Backward compatibility intentionally NOT maintained (clean break)

---

### Step 2: Split main.py into Initialization Modules
**Goal**: Break down `main.py` into focused modules

**New structure**:
```
src/initialization/
├── __init__.py              # Export all register/initialize functions
├── flask_config.py          # Flask app configuration
├── managers.py              # Auth, Settings, FileManager init
├── schedulers.py            # Scheduler + ThreadManager init
├── emitters.py              # Log and Thread emitters
├── blueprints.py            # Blueprint discovery
├── socketio_handlers.py     # SocketIO events
├── context_processors.py    # Template context injection
└── error_handlers.py        # 404, exceptions, .well-known
```

**Changes**:
1. Create initialization package with 9 modules
2. Extract logic from `main.py` to focused modules
3. Slim `main.py` to ~100 lines orchestrating initialization
4. All modules use `app_context` for state management

**Testing**: Run existing integration tests

**Outcome**: Clean architecture, Single Responsibility Principle

---

## Estimated Effort
- Step 1: ~6 hours (safer, establishes foundation)
- Step 2: ~6 hours (easier with app_context in place)
- **Total**: ~12 hours

## Benefits
1. **Testability**: Mock `app_context` once
2. **No circular imports**: Single source of truth
3. **Maintainability**: Each module has one job
4. **Type safety**: IDE autocomplete works
5. **Clean dependencies**: Explicit initialization order
