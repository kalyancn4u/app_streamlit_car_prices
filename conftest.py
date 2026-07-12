"""Make the project root importable in tests, so `from train_model import ...` works.

pytest imports this automatically before collecting tests.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
