# ParalaX Framework Refactoring Roadmap

This directory contains detailed plans for improving the framework's architecture, security, and maintainability.

## Quick Wins (Already Implemented)

- ✅ Session expiration and cleanup configured
- ✅ `util_post_to_json()` documented with debug mode
- ✅ `form_to_nested_dict()` added as simpler alternative
- ✅ `AppContext` singleton created for dependency management

---

## Refactoring Documents

### High Priority - Security

| Doc | Description | Effort | Status |
|-----|-------------|--------|--------|
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §3 | Secure secret key generation | 1h | 🔴 TODO |
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §4 | CSRF token fix (multi-tab) | 1h | 🔴 TODO |
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §6 | Rate limiting for login | 2h | 🔴 TODO |

### Medium Priority - Architecture

| Doc | Description | Effort | Status |
|-----|-------------|--------|--------|
| [01_main_py_split.md](./01_main_py_split.md) | Split main.py into initialization modules | 7h | 🔴 TODO |
| [02_app_context_migration.md](./02_app_context_migration.md) | Migrate globals to AppContext | 10h | 🟡 Started |
| [03_displayer_permission_extraction.md](./03_displayer_permission_extraction.md) | Extract permission checking | 4h | 🔴 TODO |
| [04_import_cleanup.md](./04_import_cleanup.md) | Eliminate try/except ImportError | 3h | 🔴 TODO |

### Low Priority - Polish

| Doc | Description | Effort | Status |
|-----|-------------|--------|--------|
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §2 | Thread force-kill safety | 2h | 🔴 TODO |
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §5 | Type coverage with mypy | 6h | 🔴 TODO |
| [05_minor_robustness_improvements.md](./05_minor_robustness_improvements.md) §1 | Remove Hungarian notation | 5h | 🔴 TODO |

### Future Consideration

| Doc | Description | Effort | Status |
|-----|-------------|--------|--------|
| [06_database_abstraction.md](./06_database_abstraction.md) | Storage backend abstraction | 12h | 🔵 Future |

---

## Recommended Order

### Phase 1: Security (4 hours)
1. Secure secret key generation
2. CSRF token fix
3. Rate limiting for login

### Phase 2: Core Architecture (14 hours)
1. Import cleanup (enables everything else)
2. AppContext migration
3. Split main.py

### Phase 3: Maintainability (10 hours)
1. Permission extraction
2. Type coverage

### Phase 4: Optional Polish (7 hours)
1. Thread safety improvements
2. Hungarian notation removal (if doing major version)

---

## Total Estimated Effort

| Priority | Hours |
|----------|-------|
| Security | 4h |
| Architecture | 24h |
| Polish | 13h |
| **Total** | **41h** |

---

## Notes

- All changes should be made on a feature branch
- Run full test suite after each refactoring document
- Update `copilot-instructions.md` after architectural changes
- Consider semver: breaking changes = major version bump
