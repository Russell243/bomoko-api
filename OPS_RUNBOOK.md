# Bomoko SOS - Ops Runbook

## 1) Production readiness checks

Run:

```powershell
..\venv\Scripts\python.exe manage.py sos_readiness_check
```

Expected: all checks show `[OK]`.

## 2) Twilio real delivery validation

1. Set production env vars:
`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `PUBLIC_TRACKING_BASE_URL`
2. Send one real test SOS SMS:

```powershell
..\venv\Scripts\python.exe manage.py send_sos_test_sms --to +2438XXXXXXXX
```

This command creates a temporary alert with real GPS coordinates and sends SMS through Twilio.

## 3) Multi-contact validation (real world)

1. Login as a victim account.
2. Add at least 3 trusted contacts.
3. Trigger SOS from mobile app.
4. Confirm all contacts receive SMS with:
   - emergency message,
   - public tracking link,
   - Google Maps location link.

## 4) Worker + beat continuous execution

Use docker compose for continuous tasks:

```powershell
docker compose up -d db redis backend worker beat
docker compose ps
docker compose logs -f worker
docker compose logs -f beat
```

Expected:
- `worker` consumes tasks,
- `beat` emits scheduled tasks (`retry_pending_sos_sms`, `purge_expired_sos_audio_evidence`, medical reminders).

## 5) Audio evidence retention and purge

Automatic purge is scheduled daily through Celery beat.

Manual dry-run:

```powershell
..\venv\Scripts\python.exe manage.py purge_sos_audio_evidence --dry-run
```

Manual execution:

```powershell
..\venv\Scripts\python.exe manage.py purge_sos_audio_evidence
```

Override retention window:

```powershell
..\venv\Scripts\python.exe manage.py purge_sos_audio_evidence --days 30
```

## 6) Field validation scenarios (victim-first)

Run each scenario at least once on Android and iOS:
- weak network (2G/unstable),
- temporary offline then reconnect,
- background location while app not foregrounded.

Success criteria:
- SOS alert created,
- location updates queued offline then flushed on reconnect,
- tracking page refreshes with latest coordinates,
- resolve closes alert and uploads audio evidence.

## 7) Automated API onboarding check

```powershell
..\venv\Scripts\python.exe manage.py test apps.users.tests.UsersApiTests.test_victim_onboarding_end_to_end_to_sos
```

