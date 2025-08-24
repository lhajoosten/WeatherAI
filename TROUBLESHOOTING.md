# Troubleshooting Guide

## Common Issues and Resolutions

### Location Deletion Fails with FK Constraint Error

**Problem:** DELETE /api/v1/locations/{id} returns 500 with foreign key constraint error `FK__provider___locat__02FC7413`.

**Cause:** Related records in provider_run and other tables prevent location deletion.

**Resolution:**
- Fixed in stabilization PR with manual cascade deletion
- Run database migration: `alembic upgrade head`
- If migration fails, the manual cascade in LocationRepository provides fallback
- Check logs for "Manual cascade deletion" messages

### Group Listing Returns MissingGreenlet Error

**Problem:** GET /api/v1/location-groups returns 500 with `sqlalchemy.exc.MissingGreenlet` error.

**Cause:** Lazy loading of group members in async context.

**Resolution:**
- Fixed in stabilization PR with eager loading using selectinload()
- Groups now load members properly in single query
- No code changes needed, works automatically after deployment

### Analytics Dashboard Rate Limiting

**Problem:** Opening analytics tab immediately returns 429 (Too Many Requests).

**Cause:** Multiple simultaneous analytics requests exceed rate limit.

**Resolution:**
- Analytics endpoints now have 3x higher rate limit (180/min vs 60/min)
- Use new consolidated dashboard endpoint: `/api/v1/analytics/{location_id}/dashboard`
- Dashboard endpoint includes caching to reduce repeated requests
- Consider batching frontend requests or using the single dashboard call

### CORS Errors for Angular Development

**Problem:** Frontend on localhost:4200 gets CORS errors when calling API.

**Cause:** Angular development server port not in CORS origins list.

**Resolution:**
- Added http://localhost:4200 and http://127.0.0.1:4200 to default CORS origins
- Set environment variable: `CORS_ORIGINS="http://localhost:4200,http://localhost:5173,http://localhost:3000"`
- Or rely on automatic inclusion of common development ports

### Summary Generation DateTime Error

**Problem:** Analytics summary endpoint returns 500 with "AttributeError: type object 'datetime.datetime' has no attribute 'timedelta'".

**Cause:** Incorrect import usage in SummaryPromptService.

**Resolution:**
- Fixed in stabilization PR with proper timedelta import
- No configuration changes needed
- Summary generation should work normally after deployment

### SQLAlchemy Log Spam

**Problem:** Every SQL statement is echoed to logs, causing excessive log volume.

**Cause:** Engine configured with `echo=True` or logger level set to DEBUG for 'sqlalchemy.engine'.

**Resolution:**
- Set environment variable: `SQLALCHEMY_ECHO=false` (default)
- Set environment variable: `LOG_LEVEL=INFO` (default)
- Only enable SQL logging for debugging: `SQLALCHEMY_ECHO=true`

### Datetime Comparison Errors

**Problem:** "can't compare offset-naive and offset-aware datetimes" errors during forecast & observation processing.

**Cause:** Inconsistent timezone handling when parsing ISO timestamps from external APIs.

**Resolution:**
- All datetime parsing now uses `parse_iso_utc()` helper function
- This ensures all datetimes are timezone-aware in UTC
- Provider implementations updated to use centralized parsing

### Air Quality 404 Responses

**Problem:** OpenMeteo air quality API returns 404 for some locations, logged as FAILED runs.

**Cause:** Air quality data not available for all geographic locations.

**Resolution:**
- Default behavior: 404 responses treated as NO_DATA (not failures)
- Set `OPENMETEO_AIR_QUALITY_STRICT=true` to treat 404s as failures
- Provider run status will be NO_DATA instead of FAILED for benign 404s

### Heavy Ingestion Load at Startup

**Problem:** Ingestion loop executes immediately at startup, causing perceived rate limiting.

**Cause:** No development guard and no jitter between location processes.

**Resolution:**
- Set `DISABLE_INGEST_IN_DEV=true` (default) to skip ingestion in development
- Added 0-2 second jitter between location processes
- Ingestion respects `APP_ENV=development` setting

### Location Deletion Not Working

**Problem:** DELETE requests to locations endpoint not functioning correctly.

**Cause:** Endpoint may not return proper HTTP status codes.

**Resolution:**
- DELETE /api/v1/locations/{id} now returns 204 No Content
- Verify ownership before deletion
- Returns 404 if location doesn't exist or isn't owned by user

### Location Groups Not Accessible

**Problem:** Cannot create or fetch location groups from frontend.

**Cause:** Endpoints not properly mounted or API path mismatches.

**Resolution:**
- Location group router properly mounted at /api/v1/location-groups
- Verify API base URL consistency in frontend
- Check CORS configuration includes http://127.0.0.1:5173

### MapView Not Rendering

**Problem:** Map component shows blank or broken display.

**Cause:** Missing CSS imports or container height issues.

**Resolution:**
- Ensure container has explicit height (400px)
- Add defensive null/empty location handling
- Verify react-feather icons are properly imported

### Analytics Endpoint Errors

**Problem:** Analytics endpoints returning 500 errors or empty responses.

**Cause:** Empty datasets not handled gracefully, missing ownership checks, CORS issues.

**Resolution:**
- Empty datasets now return empty arrays instead of 500 errors
- Added location ownership verification for all analytics endpoints
- CORS configured for http://localhost:5173 and http://127.0.0.1:5173
- Graceful error handling for repository exceptions

## Environment Variables

### Required for Production
- `SQLALCHEMY_ECHO=false`
- `LOG_LEVEL=INFO`
- `DISABLE_INGEST_IN_DEV=false`
- `OPENMETEO_AIR_QUALITY_STRICT=false`

### Development Settings
- `SQLALCHEMY_ECHO=false` (only enable for debugging SQL)
- `LOG_LEVEL=DEBUG` (for detailed debugging)
- `DISABLE_INGEST_IN_DEV=true` (skip heavy ingestion cycles)
- `OPENMETEO_AIR_QUALITY_STRICT=false` (lenient mode)

## Monitoring

### Key Metrics to Track
- Provider run success/failure/no_data counts
- Error message frequency for each provider
- Ingestion cycle duration and location throughput
- Analytics query response times
- Location and group operation success rates

### Log Analysis
- Structured JSON logs with correlation IDs
- Provider run summaries logged at cycle completion
- Error messages truncated to 500 characters
- Duration metrics for all major operations

## Performance Considerations

### Ingestion
- Jitter prevents burst traffic to external APIs
- Development guard reduces local testing load
- Bulk upsert operations minimize database round trips
- Error truncation prevents oversized database rows

### API Responses
- Empty data handled gracefully (no exceptions)
- Location ownership verified efficiently
- CORS properly configured for development origins
- Rate limiting enforces reasonable usage patterns