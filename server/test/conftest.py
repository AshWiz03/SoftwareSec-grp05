import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost:5000",
        help="Base URL for the target API server"
    )

@pytest.fixture
def base_url(request):
    return request.config.getoption("--base-url")

@pytest.fixture(autouse=True)
def test_notifier(request):
    # Runs before test execute
    print(f"\n[STARTING] Running test: {request.node.name}...")
    
    yield
    
    # Runs after test finishes
    print(f"[FINISHED] {request.node.name}")
