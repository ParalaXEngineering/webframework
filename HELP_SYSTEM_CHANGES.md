# Help System Changes

## Overview
Tracking modifications made to the help system during development and testing.

## Changes

### [Date: 2026-01-16] - Blueprint Name Conflict Fix

**Problem:** ValueError: The name 'help' is already registered for this blueprint
- Flask was registering two blueprints with view functions named `help()`
- Old help system in `src/pages/common.py` at `/common/help`
- New help system in `src/pages/help.py` at `/help/`

**Solution:** 
- Renamed old help function from `help()` to `help_legacy()` in [src/pages/common.py](src/pages/common.py#L231)
- This allows both help systems to coexist without endpoint conflicts
- Old URL `/common/help?topic=xyz` still works via `help_legacy` endpoint
- New URL `/help/` serves the new help system

**Files Modified:**
- `src/pages/common.py` - Renamed `help()` to `help_legacy()`
- `src/main.py` - Excluded `help.py` from auto-discovery to prevent double registration

### [Date: 2026-01-16] - Double Blueprint Registration Fix

**Problem:** ValueError: The name 'help' is already registered for this blueprint
- The `help` blueprint was being registered twice:
  1. Auto-discovery system registered all .py files in pages/ including help.py
  2. Explicit registration at line 416 for the help feature flag

**Solution:**
- Excluded `help.py` from auto-discovery in [src/main.py](src/main.py#L303)
- Added comment explaining help is registered conditionally via `m_enable_help` flag
- This allows the help system to be properly controlled by the feature flag

**Files Modified:**
- `src/main.py` - Line 303: Added `and f != 'help.py'` to exclude from auto-discovery

---

### [Date: 2026-01-16] - Breadcrumb URL Parameter Format Fix

**Problem:** BuildError when rendering help pages
- Error: "Could not build url for endpoint 'help.section_index' with values ['getting-started']"
- Breadcrumb parameters were passed as positional values `[section_id]` instead of key=value format
- Template expects parameters as strings in format `["key=value"]` to split and pass to url_for

**Solution:**
- Fixed breadcrumb calls to use proper parameter format:
  - Changed `[section_id]` to `[f"section_id={section_id}"]`
  - Changed `[section_id, page_id]` to `[f"section_id={section_id}", f"page_id={page_id}"]`
- Template now correctly builds URLs with keyword arguments

**Files Modified:**
- [src/pages/help.py](src/pages/help.py#L203) - Fixed section_index breadcrumb
- [src/pages/help.py](src/pages/help.py#L282) - Fixed page breadcrumbs

---

### [Date: 2026-01-16] - DisplayerItemCard Modern Icon-Box Upgrade

**Enhancement:** Upgraded DisplayerItemCard to use modern icon-box design pattern

**Changes:**
- Added `subtitle` parameter to DisplayerItemCard for secondary text (e.g., "5 articles")
- Redesigned card template with icon-box instead of colored header
- Icon now displayed in a rounded, semi-transparent colored box
- Better visual hierarchy with icon, title, and subtitle layout
- Added support for link buttons in footer (not just submit buttons)
- Footer buttons now support both `link` (for navigation) and form submission

**Design Improvements:**
- Icon-box with bg-opacity-10 for subtle color
- Larger icon size (1.5rem) for better visibility
- Flexbox layout for icon and title alignment
- Transparent footer background for cleaner look
- Full-width small buttons in footer

**Files Modified:**
- [src/modules/displayer/items.py](src/modules/displayer/items.py#L2132) - Added subtitle parameter to DisplayerItemCard
- [templates/displayer/items.j2](templates/displayer/items.j2#L1243) - Updated card macro with modern design and link support

---

### [Date: 2026-01-16] - Help System Refactoring - DisplayerItems Only

**Objective:** Remove all custom CSS and HTML from help.py, use only DisplayerItems

**Changes:**
1. **Section Cards** - Replaced custom HTML card with `DisplayerItemCard`
   - Uses new icon-box design
   - Includes subtitle for article count
   - Footer button links to section
   
2. **Navigation Buttons** - Replaced HTML links with `DisplayerItemButton`
   - Previous/Next page navigation
   - Back to section button
   - Proper icon positioning

3. **Content Display** - Simplified HTML wrapping
   - Removed all custom `<style>` tags
   - Kept semantic `help-content` wrapper div for framework CSS
   - Simplified TOC sidebar HTML
   
4. **Styling** - Rely on framework/theme CSS only
   - No inline styles
   - Bootstrap utility classes only
   - Clean, maintainable code

**Benefits:**
- Consistent with framework patterns
- Easier maintenance
- Better theme compatibility
- Reduced code duplication

**Files Modified:**
- [src/pages/help.py](src/pages/help.py) - Refactored index(), section_index(), and page() functions
---

### [Date: 2026-01-16] - Help Admin Page - Form Processing & Displayer Items

**Problem:** Help admin configuration page had issues:
1. Form submission used `request.form` directly instead of `util_post_to_json()`
2. Badge elements used raw HTML instead of `DisplayerItemBadge`
3. Submit buttons used raw HTML instead of `DisplayerItemButton`
4. Error saving settings due to improper form data parsing

**Solution:**
1. **Form Processing** - Use framework standard `util_post_to_json()` pattern
   - Added import: `from ..modules.utilities import util_post_to_json`
   - Changed `request.form` to `util_post_to_json(request.form.to_dict())`
   - Properly parses checkbox states for section enabled/disabled

2. **Badges** - Replaced raw HTML with `DisplayerItemBadge`
   - Source badges: `DisplayerItemBadge("Website", BSstyle.INFO)`
   - Articles count: `DisplayerItemBadge(str(count), BSstyle.LIGHT)`
   - Proper styling via BSstyle enum

3. **Buttons** - Replaced raw HTML with `DisplayerItemButton`
   - Save button: `DisplayerItemButton` with `submit=True`
   - View Help Center: `DisplayerItemButton` with `link=url_for('help.index')`, `outline=True`
   - Proper icon integration via `icon` parameter

**Benefits:**
- Form data processing follows framework patterns
- Settings save correctly without errors
- Consistent UI components across admin pages
- Better maintainability and theme compatibility

**Files Modified:**
- [src/pages/help.py](src/pages/help.py#L30) - Added util_post_to_json import
- [src/pages/help.py](src/pages/help.py#L318) - Fixed form data processing
- [src/pages/help.py](src/pages/help.py#L369) - Converted badges to DisplayerItemBadge
- [src/pages/help.py](src/pages/help.py#L388) - Converted buttons to DisplayerItemButton

---

### [Date: 2026-01-16] - TOC (Table of Contents) Documentation

**Clarification:** When does the TOC sidebar appear on help pages?

**TOC Generation:**
- The TOC sidebar appears **automatically** when markdown help files contain H2 (##) or H3 (###) headers
- The markdown library's `toc` extension generates it from these headers
- Configured in HelpManager with extension: `'toc'`
- Rendered in 2-column layout: main content (9 cols) + TOC sidebar (3 cols)

**Example Markdown with TOC:**
```markdown
# Page Title

Introduction paragraph.

## First Section
Content here...

## Second Section  
More content...

### Subsection
Details...
```

**Layout Behavior:**
- With TOC: Uses `DisplayerLayout(Layouts.HORIZONTAL, [9, 3])`
- Without TOC: Uses `DisplayerLayout(Layouts.VERTICAL, [12])`
- TOC sticky positioned at `top: 1rem` for easy navigation

**Files:**
- [src/modules/help_manager.py](src/modules/help_manager.py#L131) - TOC extension configured
- [src/modules/help_manager.py](src/modules/help_manager.py#L447) - TOC extraction: `toc = getattr(md, 'toc', '')`
- [src/pages/help.py](src/pages/help.py#L241) - TOC sidebar rendering

---

### [Date: 2026-01-16] - Settings Storage Key Format Fix

**Problem:** Error saving help section configuration
```
ERROR - help_manager - Failed to save help section config: Invalid key: help_sections
```

**Root Cause:** 
- Settings storage requires keys in `category.setting` format (minimum 2 parts)
- Help manager was using `help_sections` (single-part key)
- Settings storage validates that both category and setting exist before allowing writes

**Solution:**
1. **Changed CONFIG_KEY** from `"help_sections"` to `"help.enabled_sections"`
2. **Auto-create help category** if it doesn't exist when saving
3. **Simplified data structure** - store dict of `{section_id: enabled}` directly in value field

**Implementation Details:**
- `CONFIG_CATEGORY = "help"` - category name
- `CONFIG_KEY = "help.enabled_sections"` - full key path
- `save_section_config()` creates category with proper structure if missing:
  ```python
  {
    "help": {
      "friendly": "Help System",
      "enabled_sections": {
        "friendly": "Enabled Sections",
        "type": "dict",
        "value": {section_id: true/false, ...},
        "persistent": true
      }
    }
  }
  ```
- `_load_section_config()` directly reads from `value` field

**Files Modified:**
- [src/modules/help_manager.py](src/modules/help_manager.py#L101) - Changed CONFIG_KEY constant
- [src/modules/help_manager.py](src/modules/help_manager.py#L327) - Updated _load_section_config
- [src/modules/help_manager.py](src/modules/help_manager.py#L342) - Updated save_section_config with auto-create

---

### [Date: 2026-01-16] - Checkbox Data Parsing Fix

**Problem:** Enabled checkboxes always saved as unchecked

**Root Cause:** 
`util_post_to_json()` has special handling for checkboxes with value "on":
- Checkbox `name="section_getting-started" value="on"` gets transformed
- Splits on underscore: `"section_getting-started": "on"` → `{"section": ["getting-started"]}`
- Old code checked `if "section_getting-started" in data` which was always False after transformation

**Solution:**
Extract the array of enabled section IDs from the transformed data structure:
```python
data = util_post_to_json(request.form.to_dict())
enabled_sections = data.get('section', [])  # Get the array
section_states[section.id] = section.id in enabled_sections  # Check membership
```

**Files Modified:**
- [src/pages/help.py](src/pages/help.py#L315) - Fixed checkbox data extraction from util_post_to_json result

