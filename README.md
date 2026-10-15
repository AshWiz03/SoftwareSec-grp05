# tatou
A web platform for pdf watermarking. This project is intended for pedagogical use, and contain security vulnerabilities. Do not deploy on an open network.

## Prerequisites
 
- Docker and Docker Compose
- Git
- Python 3.12 (only for running without Docker)
- pytest (For running tests locally against the docker server (localhost))

## Instructions

The following instructions are meant for a bash terminal on a Linux machine. If you are using something else, you will need to adapt them.

To clone the repo, you can simply run:

```bash
git clone https://github.com/AshWiz03/SoftwareSec-grp05.git
```

Note that you should probably fork the repo and clone your own repo

# Configuration
 
Clone the repository and create the environment file:
 
```bash
git clone <your-group-repo-url>
cd <repository-folder>
```
 
Create a file named `.env` in the repository root (it is gitignored and must never be committed) with the following variables:
 
```dotenv
MARIADB_ROOT_PASSWORD=<choose-a-password>
MARIADB_USER=<choose-a-username>
MARIADB_PASSWORD=<choose-a-password>
SECRET_KEY=<long-random-string>
SERVER_KEY_PASSPHRASE=<passphrase-of-server_priv.asc>
FLAG_2=<flag-value>
```
 
The server's private RMAP key `server/keys/server_priv.asc` is not committed. Place it in `server/keys/` before building. The public keys and the test client key pair (`test_group_priv.asc` / `test_group_pub.asc`) are committed.

## Deployment
 
```bash
# Build the images and start all containers
docker compose up --build -d
 
# Follow the logs
docker compose logs -f
 
# Check that the API is up
curl -v http://127.0.0.1:5000/healthz
```
Open http://127.0.0.1:5000 in a browser to use the web interface

> Note: `docker compose up` also starts the `tests` and `mutation` services, which run the test suites once and then exit. See below.

## Testing
 
### Unit and API tests
 
The API test suite in `server/test/` sends HTTP requests to the running server. It runs in the `tests` container, which waits for the server to be healthy.
 
Run the full suite:
 
```bash
docker compose up --build tests
```
 
Results are written as JUnit XML to `unit_test_results/results_<timestamp>.xml`.
 
Run a single test file or test:
 
```bash
docker compose run --rm tests pytest test/test_auth.py -svv --base-url=http://server:5000
docker compose run --rm tests pytest test -svv --base-url=http://server:5000 -k test_login_success
```
 
Tests marked `@pytest.mark.manual` are excluded from automated runs.
 
### In-process unit tests
 
The suite in `mutation/test/` calls the Flask app directly through `app.test_client()` instead of over HTTP, and tests `validation.py` and `server.py` functions directly. It runs in the `mutation` container. You can run it as a normal pytest suite, without any mutation testing:
 
```bash
# Run all in-process tests
docker compose run --rm mutation python -m pytest test/ -v
 
# Run a single test file
docker compose run --rm mutation python -m pytest test/test_validation_mutation.py -v
 
# Run tests matching a string
docker compose run --rm mutation python -m pytest test/ -v -k validate_password
```
 
These tests need the database, so the `db` container starts automatically.

### Mutation testing
 
Mutation testing uses mutmut. It mutates `server/src/validation.py` and `server/src/server.py` and runs the in-process test suite in `mutation/test/` against each mutant.
 
Configuration is in `mutation/setup.cfg`.
 
Run mutation testing:
 
```bash
docker compose up --build mutation
```

Results are written to `mutation_test_results/`:
 
| File | Content |
|---|---|
| `results_<timestamp>.txt` | Every mutant that was not killed, with its status |
| `survivors_<timestamp>.txt` | The diff of each surviving mutant |

### Running locally without Docker

With the server running via docker, run the API tests against it:
 
```bash
cd ./server/test/
pytest <test-filename.py> -svv --base-url http://localhost:5000
```
## Continuous integration
 
GitHub Actions (`.github/workflows/tests.yml`) runs on every pull request and on pushes to `main`:
 
1. Creates `.env` and restores the private keys and env variables from repository secrets.
2. Runs the API test suite. A failing test fails the check.
3. Publishes the test results on the pull request and uploads `unit_test_results/` as an artifact.

Mutation testing is not part of CI. Run it locally as described in [Mutation testing](#mutation-testing).
 
Required repository secrets: `MARIADB_ROOT_PASSWORD`, `MARIADB_USER`, `MARIADB_PASSWORD`, `SECRET_KEY`, `SERVER_KEY_PASSPHRASE`, `SERVER_PRIV_B64` (base64 of `server_priv.asc`) and `TEST_PRIV_64` (base64 of `test_group_priv.asc`).

### Coverage analysis
 
Coverage is measured with the in-process test suite in `mutation/test/`, since those tests execute the server code in the same process. The HTTP-based suite cannot measure server coverage because the code runs in a different container.
 
```bash
docker compose run --rm mutation sh -c "pip install pytest-cov && python -m pytest test/ --cov=server --cov=validation --cov-report=term-missing --cov-report=html:/app/mutation_test_results/coverage"
```
 
The HTML report is written to `mutation_test_results/coverage/index.html`.



