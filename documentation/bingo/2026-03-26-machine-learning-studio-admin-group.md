# BINGO: Machine Learning Studio Admin Group

**Date:** 2026-03-26
**Status:** Complete and verified
**Branch:** commit-changes

---

## Screenshot

![Machine Learning Studio Admin Group](../images/ml-studio-admin-group-2026-03-26.png)

---

## Problem

ML-related models (MLEngine, MLDataset, MLTaxonomy, DeepSeekPrompt) were scattered in the "Dose" admin section instead of being grouped logically together.

## Solution

Created a new Django app `ml_studio` with proxy models to group all ML-related admin UIs under a single "Machine Learning Studio" section in the admin sidebar.

---

## What Was Done

### 1. Created `ml_studio/` App

New app with proxy models that don't create new database tables - they just provide a way to register the same models under a different admin section.

**Files created:**
- `ml_studio/__init__.py` - App initialization
- `ml_studio/apps.py` - AppConfig with `verbose_name = 'Machine Learning Studio'`
- `ml_studio/models.py` - Proxy models (MLEngineProxy, MLTaxonomyProxy, MLDatasetProxy, MLPromptProxy)
- `ml_studio/admin.py` - Admin registrations with proper fieldsets and icons

### 2. Proxy Models

```python
class MLEngineProxy(MLEngine):
    class Meta:
        proxy = True
        verbose_name = 'ML Engine'
        verbose_name_plural = 'ML Engines'

class MLTaxonomyProxy(MLTaxonomy):
    class Meta:
        proxy = True
        verbose_name = 'ML Taxonomy'
        verbose_name_plural = 'ML Taxonomies'

class MLDatasetProxy(MLDataset):
    class Meta:
        proxy = True
        verbose_name = 'ML Dataset'
        verbose_name_plural = 'ML Datasets'

class MLPromptProxy(DeepSeekPrompt):
    class Meta:
        proxy = True
        verbose_name = 'ML Prompt'
        verbose_name_plural = 'ML Prompts'
```

### 3. Settings Configuration

Added to `mysite/settings.py`:

```python
# In INSTALLED_APPS
'ml_studio',  # Machine Learning Studio - grouped ML models

# In JAZZMIN_SETTINGS icons
"ml_studio.mlengineproxy": "fas fa-brain",
"ml_studio.mltaxonomyproxy": "fas fa-project-diagram",
"ml_studio.mldatasetproxy": "fas fa-database",
"ml_studio.mlpromptproxy": "fas fa-robot",

# Hide original models from Dose section
"hide_models": [
    "dose.mlengine",
    "dose.mltaxonomy",
    "dose.mldataset",
    "dose.deepseekprompt",
],
```

---

## Files Modified/Created

| File | Change |
|------|--------|
| `ml_studio/__init__.py` | New - App initialization |
| `ml_studio/apps.py` | New - AppConfig |
| `ml_studio/models.py` | New - Proxy models |
| `ml_studio/admin.py` | New - Admin registrations |
| `mysite/settings.py` | Added ml_studio to INSTALLED_APPS, icons, hide_models |

---

## Result in Admin Sidebar

```
Machine Learning Studio
├── ML Datasets (fas fa-database)
├── ML Engines (fas fa-brain)
├── ML Prompts (fas fa-robot)
└── ML Taxonomies (fas fa-project-diagram)
```

---

## Verification

1. Hard refresh admin page (Ctrl+Shift+R)
2. "Machine Learning Studio" section should appear in sidebar
3. ML Datasets, ML Engines, ML Prompts, ML Taxonomies should be listed under it
4. Original models should NOT appear under "Dose" section

---

## Notes

- Proxy models don't require migrations - they use the same database tables
- The `hide_models` Jazzmin setting hides the original models from the Dose section
- Icons are configured for visual consistency with existing admin UI
