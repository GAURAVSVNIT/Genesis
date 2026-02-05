# Genesis Backend

This is the Python backend service for the Genesis system.

## Project Structure

- **api/**: API endpoints and routers.
- **core/**: Core system logic and configuration.
- **database/**: Database models and connections.
- **scripts/**: Utility scripts for maintenance and migrations.
- **tests/**: Test suite.
- **docs/**: Backend-specific documentation.

## Running the Backend

Ensure you have the dependencies installed:

```sh
pip install -r requirements.txt
```

Run the application:

```sh
python main.py
```

## Scripts

Utility scripts are located in the `scripts/` directory. Run them from the `apps/backend` directory:

```sh
python scripts/audit_metrics.py
```
