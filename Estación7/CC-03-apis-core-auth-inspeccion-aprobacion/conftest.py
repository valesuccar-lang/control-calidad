import sys
import os

# CC-03 tests use the app from Estación5 (complete implementation)
# CC-03/app/routes/auth.py re-exports the router from there
_base = os.path.join(os.path.dirname(__file__), "..", "..", "Estación5", "Control-Calidad")
sys.path.insert(0, os.path.abspath(_base))
# Remove the local CC-03/app from path so Estación5/app takes precedence
_local_app = os.path.join(os.path.dirname(__file__))
if _local_app in sys.path:
    sys.path.remove(_local_app)
