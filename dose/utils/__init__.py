from dose.utils.secret_manager import get_secret, sm, clear_cache

import importlib, os, sys

_utils_py = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils.py')
if os.path.exists(_utils_py):
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('dose._utils_flat', _utils_py)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    for _name in dir(_mod):
        if not _name.startswith('_'):
            globals()[_name] = getattr(_mod, _name)
    del _spec, _mod, _name
del _utils_py, _ilu
