# DEPRECATED - Use src.modules.threaded instead# DEPRECATED - Use src.modules.threaded instead

import warningsimport warnings

from .threaded.threaded_manager import Threaded_manager, thread_manager_objfrom .threaded.threaded_manager import Threaded_manager, thread_manager_obj

warnings.warn('Use src.modules.threaded instead', DeprecationWarning, 2)warnings.warn('Use src.modules.threaded instead', DeprecationWarning, 2)

__all__ = ['Threaded_manager', 'thread_manager_obj']__all__ = ['Threaded_manager', 'thread_manager_obj']

