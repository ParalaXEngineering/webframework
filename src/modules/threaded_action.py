# DEPRECATED - Use src.modules.threaded instead# DEPRECATED - Use src.modules.threaded instead

import warningsimport warnings

from .threaded.threaded_action import Threaded_actionfrom .threaded.threaded_action import Threaded_action

warnings.warn('Use src.modules.threaded instead', DeprecationWarning, 2)warnings.warn('Use src.modules.threaded instead', DeprecationWarning, 2)

__all__ = ['Threaded_action']__all__ = ['Threaded_action']

