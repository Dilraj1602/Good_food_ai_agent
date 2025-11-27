import sys, importlib, pathlib

proj = pathlib.Path(__file__).resolve().parents[1]
if str(proj) not in sys.path:
    sys.path.insert(0, str(proj))

print('Python executable:', sys.executable)
print('Python version:', sys.version.splitlines()[0])

try:
    m = importlib.import_module('app.controller')
    print('Imported app.controller successfully; has handle_message =', hasattr(m, 'handle_message'))
except Exception as e:
    print('Import FAILED:', repr(e))
    raise
