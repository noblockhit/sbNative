try:
    from . import debugtools
    from . import runtimetools
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(__file__))
    import debugtools
    import runtimetools
