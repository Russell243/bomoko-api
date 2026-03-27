# Bomoko - Checklist Implementation (victimes prioritaire)

Date de mise a jour: 2026-03-25

## Priorite terrain-victime

- [ ] Configurer Twilio en production (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`, `PUBLIC_TRACKING_BASE_URL`) et valider envoi reel.
- [ ] Valider envoi multi-contacts en conditions reelles (minimum 3 contacts).
- [x] Commande de validation Twilio disponible (`manage.py send_sos_test_sms --to +243...`).
- [x] Page publique de tracking SOS finalisee (statut, coordonnees, refresh 15s, bouton Google Maps).
- [x] Lien SMS de suivi public route vers la page terrain (`/track/{alert_id}/{token}/`).
- [x] Enregistrement audio automatique au declenchement SOS cote mobile.
- [x] Upload audio automatique a la resolution SOS.
- [x] Historique audio prive (lecture/suppression) disponible pour la victime.
- [x] Chiffrement audio cote backend actif (`SOS_AUDIO_ENCRYPTION_ENABLED`).
- [ ] Test terrain SOS en reseau faible / offline / reprise reseau.
- [ ] Validation Android/iOS du tracking en background (position + file offline).
- [ ] Worker + beat en continu en production.
- [x] Politique de retention des preuves appliquee (purge auto Celery + commande manuelle).
- [x] UX SOS impose au moins 3 contacts pour declencher.
- [x] Onboarding API bout-en-bout teste automatiquement (register -> login -> profile -> SOS).
- [ ] Validation onboarding complet en conditions reelles (terrain).

## Sprint 4 (etat)

- [x] Notifications push server-to-device operationnelles.
- [x] Premier lot de regles metier actif sur forum.
- [x] Premier lot de regles metier actif sur legal.
- [x] Premier lot de regles metier actif sur medical.
- [ ] Module medical complet: rappels RDV + parcours de prise en charge (phase 2 UX/metier).
- [ ] Module juridique complet: workflow avance de suivi dossier (phase 2 UX/metier).

## Notes de reprise

- Front mobile SOS: `C:\Bomoko\bomoko-mobile\app\(tabs)\sos.tsx`
- Tracking public backend: `C:\Bomoko\bomoko-api\apps\sos\views.py`, `C:\Bomoko\bomoko-api\templates\sos\public_tracking.html`
- SMS service: `C:\Bomoko\bomoko-api\apps\sos\services.py`
- Ops runbook: `C:\Bomoko\bomoko-api\OPS_RUNBOOK.md`
