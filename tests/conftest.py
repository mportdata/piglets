from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

@pytest.fixture
def model_name() -> str:
    return "gpt-5.2"

@pytest.fixture
def natural_language_query() -> str:
    return "Which tags saw the largest increase in average answer score from 2022 to 2023, considering only questions with at least 5 answers?"