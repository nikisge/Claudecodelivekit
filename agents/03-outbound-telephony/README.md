# Agent 03 — Outbound Lead Qualifier

Voice-Agent, der bei einem Formular-Submit im Frontend automatisch einen Outbound-Call
über Twilio SIP auslöst, den Lead qualifiziert und das Ergebnis live ans Frontend zurückgibt.

## Flow

```
User füllt Formular    →   Frontend /api/dispatch-call    →   LiveKit SIP Trunk    →    Handy klingelt
                                        │
                                        ├─ erstellt Room
                                        ├─ dispatcht Agent mit Name + Phone + Kontext
                                        └─ erstellt SIPParticipant (löst Anruf aus)
                                                  │
                                                  └─ Agent qualifiziert Lead
                                                           │
                                                           └─ save_lead → Data-Channel → Frontend zeigt JSON
```

## Voraussetzungen

- **Nur auf VPS sinnvoll** — lokal auf dem Mac kann Twilio den SIP-Trunk nicht erreichen (ausser über ngrok; separat dokumentiert).
- Twilio-Account mit Elastic SIP Trunk, konfiguriert auf VPS-IP.
- LiveKit-SIP-Komponente läuft (siehe `docker-compose.yml`).
- Einmaliges Setup: `python scripts/setup-sip.py` ausführen, um den Outbound-Trunk in LiveKit anzulegen und die resultierende `LIVEKIT_OUTBOUND_TRUNK_ID` in `.env` einzutragen.

Details: `docs/twilio-setup.md`.

## Gespräch

Der Agent stellt 4 Qualifikations-Fragen und ruft am Ende `save_lead` auf. Das Ergebnis wird als Data-Message an das Frontend gepusht:

```json
{
  "type": "lead_qualified",
  "data": {
    "budget_eur": "5-20k",
    "timeline": "Q3 2026",
    "use_case": "DSGVO-konformer Voice-Bot für Arztpraxis",
    "interest_level": "hoch",
    "is_decision_maker": true,
    "notes": "Praxis-Inhaber, will nächste Woche Demo"
  }
}
```

## DSGVO

- **Vertex AI:** EU-Region wie `europe-west4` setzen
- **Azure Speech:** Speech-Resource in EU-Region für STT/TTS; ElevenLabs nur optional mit Enterprise EU Residency + Zero-Retention
- **Twilio:** DPA abschließen, EU-Rechenzentrum (Frankfurt/Dublin) wählen. Call-Recording ist in diesem Agent standardmäßig aus
