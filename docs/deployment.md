# Google Cloud Run + Cloud SQL Deployment Log

This document records the specific infrastructure and configuration challenges encountered during the deployment of the FP&A Platform to Google Cloud Run and Cloud SQL, alongside their resolutions. This log serves as an operational runbook for future deployments.

## 1. Cloud SQL Micro Instance Creation Failure
**Symptom:** Creating the Cloud SQL instance with `--tier=db-f1-micro` failed.
**Cause:** The default database edition (ENTERPRISE_PLUS) does not support the legacy `db-f1-micro` tier.
**Fix:** Explicitly set the edition when creating the instance by appending the `--edition=ENTERPRISE` flag.

## 2. Cloud Build Service Account Permissions
**Symptom:** Source-based deployments failed with a 403 Forbidden error (`storage.objects.get`) during the build phase.
**Cause:** The source deploy process executes using the default compute service account, which lacked read access to the Cloud Storage bucket containing the source code.
**Fix:** Granted the `roles/cloudbuild.builds.builder` role to the default compute service account.

## 3. PowerShell Environment Variable Parsing
**Symptom:** The `CLOUD_SQL_CONNECTION_NAME` variable was corrupted upon deployment, preventing database connections.
**Cause:** Unquoted commas in the `--set-env-vars` flag were parsed by PowerShell as an array, causing the variables to be space-joined rather than comma-separated.
**Fix:** Enclosed the entire `--set-env-vars` flag value in explicit quotes (e.g., `--set-env-vars="VAR1=val,VAR2=val"`) to prevent PowerShell from misinterpreting the commas.

## 4. Cloud Run to Cloud SQL Networking
**Symptom:** The backend could not connect to the database via standard TCP.
**Cause:** Cloud Run requires connecting to Cloud SQL via a Unix socket (`/cloudsql/PROJECT:REGION:INSTANCE`) rather than a TCP port.
**Fix:** 
1. Attached the Cloud SQL instance to the Cloud Run service via the `--add-cloudsql-instances` flag.
2. Injected the `CLOUD_SQL_CONNECTION_NAME` environment variable.
3. Updated `database.py` to dynamically switch the SQLAlchemy connection string from TCP to a Unix socket when the `CLOUD_SQL_CONNECTION_NAME` is detected.

## 5. Database Authentication Failures
**Symptom:** Authentication failures occurring despite correct credentials in Secret Manager.
**Cause:** Non-alphanumeric special characters in the database password were unescaped in the SQLAlchemy connection URL, breaking the URI structure.
**Fix:** Unified the database password and the Secret Manager secret to a secure alphanumeric value. (Note: A more robust hardening strategy is to strictly URL-encode the credentials prior to injecting them into the SQLAlchemy URI).

## 6. Nginx Port Binding on Cloud Run
**Symptom:** The frontend container deployed but failed health checks because it was listening on port 80 instead of Cloud Run's dynamic `$PORT`.
**Cause:** Cloud Run injects a `$PORT` environment variable (default 8080) that the container must bind to.
**Fix:** Created a custom `nginx.conf.template` and implemented a Dockerfile entrypoint leveraging `envsubst '${PORT}'`. By restricting substitution strictly to `${PORT}`, Nginx's internal routing variables (`$uri`, `$host`) were preserved, allowing SPA `try_files` routing to function seamlessly.

## 7. Phase 2 Deployment
The cloud database was reset to a clean state for the Phase 2 schema additions. A dedicated `reset_db.py` script (`drop_all` + `create_all`) was run securely against the remote database via the Cloud SQL Auth Proxy. After re-seeding the data, the backend and frontend were redeployed live using the exact same deployment commands established in Phase 1.

## 8. Phase 3 Deployment
The cloud DB was reset and re-seeded via the Cloud SQL Auth Proxy to pick up the new integration tables (`ExternalMapping`, `SyncRun`) and the new `ActualLine.source` column. Afterward, the backend and frontend were redeployed to make the ERP Integration layer live.

---

## Additional Operational Notes
- **CORS Configuration:** As a public read-only demo, the backend CORS middleware was explicitly set to `allow_origins=["*"]` with `allow_credentials=False`. (Combining wildcard origins with `allow_credentials=True` is an invalid configuration rejected by browsers).
- **Database Seeding:** Production data seeding was executed securely from a local machine using the Google Cloud SQL Auth Proxy, bypassing the need for public IP exposure or complex VPC peering.
