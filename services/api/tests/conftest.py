import os, tempfile, sys
from pathlib import Path
# Isolated test DB, never touch local developer data.
DBFILE=Path(tempfile.mkdtemp(prefix="pipmora-tests-"))/"tests.sqlite"
os.environ["DATABASE_URL"]="sqlite:///"+str(DBFILE)
os.environ["APP_ENV"]="development"
os.environ["ENABLE_DEV_RESET_LINK"]="true"
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from app.main import app
@pytest.fixture
def client():
    with TestClient(app) as c:yield c
