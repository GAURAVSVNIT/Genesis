---
description: Debug backend startup in Turbo repo
---

## Steps to isolate and run the backend independently

1. **Activate the Python virtual environment**

   ```bash
   cd d:/CODING/Genesis/apps/backend
   .venv\Scripts\activate
   ```

   // turbo
2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   // turbo
3. **Run the backend directly with uvicorn**

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

   // turbo
   Verify you see `Uvicorn running on http://0.0.0.0:8000`.

4. **Run the backend via pnpm (Turbo) to ensure the script works**

   ```bash
   pnpm run dev
   ```

   // turbo
   This will invoke the `dev` script defined in `apps/backend/package.json` which simply calls the same uvicorn command.

5. **If the above works, test the whole repo but skip failing packages**

   ```bash
   # Skip docs (port conflict) and run only backend & frontend
   turbo run dev --filter "backend..." "frontend..."
   ```

   // turbo
   This isolates the backend and frontend, avoiding the docs package that currently fails on port 3001.

6. **Resolve port conflicts**
   - Identify which process is using port 3000 or 3001:

     ```bash
     netstat -ano | findstr :3000
     netstat -ano | findstr :3001
     ```

   - Kill the offending PID (replace `<PID>`):

     ```bash
     taskkill /PID <PID> /F
     ```

   - Or change the ports in `apps/frontend/.env` or `apps/docs/.env`.

7. **Optional: Update `turbo.json` to ignore docs during dev**

   ```json
   {
     "$schema": "https://turborepo.com/schema.json",
     "ui": "tui",
     "tasks": {
       "dev": {
         "cache": false,
         "persistent": true,
         "dependsOn": [],
         "outputs": []
       }
     },
     "pipeline": {
       "dev": {
         "exclude": ["docs"]
       }
     }
   }
   ```

   // turbo
   This prevents the docs package from being executed when you run `turbo run dev`.

## Verification

- After step 3 you should see a log line like:
  `INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`
- Access `http://localhost:8000` in a browser; you should receive a JSON response from FastAPI (e.g., `{"message":"Hello World"}` if you add a simple route).
- If step 5 succeeds, the backend is correctly integrated with Turbo.

---
