import sys
from pathlib import Path

# Allow importing project modules from src/ and reusing my_test.py logic
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from test import my_test  # type: ignore


def test_full_onlyoffice_flow():
    """
    Запускает полный E2E сценарий из test/my_test.py под управлением pytest.
    """
    my_test.main()
