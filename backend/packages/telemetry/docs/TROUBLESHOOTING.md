# Cloud Logging Troubleshooting Guide

This guide helps diagnose and resolve common issues when using the Cloud Logging exporters with CliniCraft's telemetry system.

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Permission Issues](#permission-issues)
- [Configuration Issues](#configuration-issues)
- [Common Error Messages](#common-error-messages)
- [Verification Steps](#verification-steps)
- [Performance Issues](#performance-issues)

---

## Authentication Issues

### Symptom: "Could not automatically determine credentials"

**Cause**: Application Default Credentials (ADC) not configured.

**Solution**:
```bash
# For local development - login with your Google account
gcloud auth application-default login

# For production - ensure service account key is configured
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**Verification**:
```bash
# Check current ADC status
gcloud auth application-default print-access-token

# Should print an access token without errors
```

### Symptom: "The caller does not have permission"

**Cause**: Authenticated identity lacks necessary IAM roles.

**Solution**: Grant the `roles/logging.logWriter` role to your identity:
```bash
# For user accounts
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:YOUR_EMAIL@example.com" \
  --role="roles/logging.logWriter"

# For service accounts
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"
```

---

## Permission Issues

### Required IAM Roles

The identity running your application needs:
- **`roles/logging.logWriter`** - Write logs to Cloud Logging
- **`roles/cloudtrace.agent`** (optional) - For trace correlation

### Checking Current Permissions

```bash
# Check project-level permissions for user
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL@example.com"

# Check permissions for service account
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:SERVICE_ACCOUNT@PROJECT_ID.iam.gserviceaccount.com"
```

### Missing Project Access

**Symptom**: "Project not found" or "Permission denied"

**Cause**: Identity doesn't have access to the GCP project.

**Solution**:
```bash
# List projects you have access to
gcloud projects list

# Verify project exists and is accessible
gcloud projects describe PROJECT_ID
```

---

## Configuration Issues

### Missing GCP_PROJECT_ID

**Symptom**: Application fails to initialize Cloud Logging exporter.

**Cause**: `GCP_PROJECT_ID` environment variable not set.

**Solution**:
```bash
# Set project ID for current session
export GCP_PROJECT_ID="your-project-id"

# Or add to .env file (backend/.env)
echo "GCP_PROJECT_ID=your-project-id" >> backend/.env
```

**Verification**:
```bash
# Check environment variable is set
echo $GCP_PROJECT_ID

# Should print your project ID
```

### Invalid Log Names

**Symptom**: "Invalid log name format" error.

**Cause**: Log names must match Cloud Logging naming requirements:
- Only alphanumeric characters, hyphens, underscores, periods
- Cannot start with `goog` or contain `google`
- Max 512 characters

**Valid examples**:
- `clinicraft-dev`
- `my-application-logs`
- `backend_logs`

**Invalid examples**:
- `google-logs` (contains "google")
- `logs/with/slashes` (invalid characters)

### Environment Variable Precedence

Configuration is loaded in this order (later overrides earlier):
1. Default values in `config.py`
2. `.env` file in `backend/` directory
3. System environment variables
4. Explicitly passed parameters

---

## Common Error Messages

### "Invalid log name"

**Full error**: `google.api_core.exceptions.InvalidArgument: 400 Invalid log name`

**Root cause**: Log name doesn't follow Cloud Logging naming rules.

**Solution**: Use valid log name format (alphanumeric, hyphens, underscores only):
```python
exporter = CloudLoggingLogExporter(
    project_id="my-project",
    log_name="clinicraft-dev"  # Valid format
)
```

### "Permission denied"

**Full error**: `google.api_core.exceptions.PermissionDenied: 403 Permission denied`

**Root cause**: Missing `roles/logging.logWriter` IAM role.

**Solution**: Grant logging permissions (see [Permission Issues](#permission-issues)).

### "Project not found"

**Full error**: `google.api_core.exceptions.NotFound: 404 Project not found`

**Root causes**:
1. Project ID is incorrect
2. Identity doesn't have access to project
3. Project has been deleted

**Solution**:
```bash
# Verify project exists
gcloud projects list --filter="projectId:PROJECT_ID"

# Check you have access
gcloud projects describe PROJECT_ID
```

### "Failed to export logs/spans to Cloud Logging"

**Symptom**: Warning logged in application logs.

**Root cause**: Cloud Logging API call failed (network, auth, or API issue).

**Debugging**:
1. Check Python logging output for detailed exception
2. Verify network connectivity to Google APIs
3. Test authentication (see [Authentication Issues](#authentication-issues))
4. Check Cloud Logging API is enabled:
   ```bash
   gcloud services enable logging.googleapis.com --project=PROJECT_ID
   ```

---

## Verification Steps

### 1. Verify Logs Are Reaching Cloud Logging

**Using GCP Console**:
1. Go to [Cloud Logging](https://console.cloud.google.com/logs)
2. Select your project
3. Use query to find your logs:
   ```
   logName="projects/PROJECT_ID/logs/clinicraft-dev"
   resource.type="global"
   ```

**Using gcloud CLI**:
```bash
# List recent logs
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev" \
  --limit=10 \
  --format=json

# Filter by severity
gcloud logging read "logName=projects/PROJECT_ID/logs/clinicraft-dev AND severity>=ERROR" \
  --limit=10
```

### 2. Testing with TELEMETRY=cloudlogging

**Local testing**:
```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export TELEMETRY=cloudlogging

# Run application
cd backend
uv run uvicorn app.main:app --reload

# Generate test logs
curl http://localhost:8000/health
```

**Check logs in Cloud Logging**:
```bash
# Wait a few seconds for export, then check
gcloud logging read "logName=projects/$GCP_PROJECT_ID/logs/clinicraft-dev" \
  --limit=5 \
  --format="table(timestamp, severity, jsonPayload.message)"
```

### 3. Verify Trace Correlation

**Check traces are linked to logs**:
1. Find a trace ID from your application logs
2. Query Cloud Logging with trace filter:
   ```bash
   gcloud logging read "trace=projects/PROJECT_ID/traces/TRACE_ID" \
     --limit=10
   ```

**Using Cloud Console**:
1. Go to [Trace List](https://console.cloud.google.com/traces)
2. Click on a trace
3. View associated logs in the trace details

### 4. End-to-End Test Script

```bash
#!/bin/bash
# test-cloud-logging.sh - Verify Cloud Logging integration

set -e

echo "1. Checking authentication..."
gcloud auth application-default print-access-token > /dev/null
echo "✓ Authentication configured"

echo "2. Checking project access..."
gcloud projects describe "$GCP_PROJECT_ID" > /dev/null
echo "✓ Project accessible"

echo "3. Checking IAM permissions..."
# This will error if you don't have logging.logWriter
gcloud projects get-iam-policy "$GCP_PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/logging.logWriter" > /dev/null
echo "✓ Logging permissions configured"

echo "4. Testing log write..."
export TELEMETRY=cloudlogging
cd backend
uv run python -c "
from telemetry import get_logger
logger = get_logger('test')
logger.info('Test log from troubleshooting script')
print('✓ Log exported successfully')
"

echo "5. Verifying log in Cloud Logging (waiting 5s)..."
sleep 5
gcloud logging read "logName=projects/$GCP_PROJECT_ID/logs/clinicraft-dev AND jsonPayload.message:'Test log from troubleshooting script'" \
  --limit=1 \
  --format="value(jsonPayload.message)"

echo "✓ All checks passed!"
```

---

## Performance Issues

### High Latency from Cloud Logging API

**Symptom**: Application feels slow or logs take time to appear.

**Causes**:
1. Network latency to Google APIs
2. Too many sequential API calls
3. Large log payloads

**Current implementation**: Sequential writes (one API call per log/span)

**Mitigation**:
- Use async exporters (OpenTelemetry batch processors)
- Adjust batch processor settings in `telemetry_config.py`:
  ```python
  from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

  processor = BatchLogRecordProcessor(
      exporter,
      max_queue_size=2048,      # Increase buffer
      schedule_delay_millis=5000,  # Batch every 5s
      max_export_batch_size=512    # Larger batches
  )
  ```

**Future optimization**: Use Cloud Logging batch API (tracked in Phase 3 plan).

### Network Connectivity Problems

**Symptom**: Intermittent failures, timeouts.

**Debugging**:
```bash
# Test connectivity to Google APIs
curl -I https://logging.googleapis.com/

# Check DNS resolution
nslookup logging.googleapis.com

# Test with explicit timeout
gcloud logging write test-log "test message" --timeout=5s
```

**Solutions**:
- Check firewall rules allow HTTPS (443) to Google APIs
- Verify no proxy issues blocking googleapis.com
- Consider VPC Service Controls if using private Google access

### Too Many Logs Generated

**Symptom**: High Cloud Logging costs, quota issues.

**Solutions**:
1. **Filter logs by severity**:
   ```bash
   # Only export ERROR and above
   export LOG_LEVEL=ERROR
   ```

2. **Sample logs**:
   ```python
   # In telemetry_config.py
   from opentelemetry.sdk._logs import LoggerProvider
   from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor

   # Use sampling (custom implementation needed)
   ```

3. **Use exclusion filters** in Cloud Logging:
   - Go to [Logs Router](https://console.cloud.google.com/logs/router)
   - Create exclusion filters for noisy logs
   - Exclude health checks, debug logs, etc.

---

## Additional Resources

- [Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/languages/python/)
- [CliniCraft Telemetry README](../README.md)
- [Phase 3 Plan](../../../../docs/development/telemetry-cloud-logging/PHASE_3_plan.md) - E2E testing details

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check application logs** for detailed error messages
2. **Enable debug logging**:
   ```bash
   export LOG_LEVEL=DEBUG
   export TELEMETRY=cloudlogging
   ```
3. **Run readiness checks**:
   ```bash
   ./scripts/check-readiness.sh
   ```
4. **Review GCP project settings** in Cloud Console
5. **File an issue** with reproduction steps and error logs

---

*Last updated: 2025-11-08*
