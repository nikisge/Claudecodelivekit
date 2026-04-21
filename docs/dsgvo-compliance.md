# DSGVO-Konformität — Provider-Übersicht

Dieses Repo ist darauf ausgelegt, nur mit EU-Region-Endpoints oder Zero-Retention-Modes zu arbeiten. Kein Provider ist „automatisch" DSGVO-konform — du musst aktiv die richtige Region / das richtige Deployment konfigurieren. Diese Seite listet auf, worauf du pro Provider achten musst.

## Übersicht

| Komponente | Provider | DSGVO-Konfiguration |
|---|---|---|
| LLM Agent 01 | Google Vertex AI — Gemini 2.5 Flash Lite | `europe-west4` (Niederlande) oder `europe-west1` (Belgien) |
| LLM Agent 02+03 | Azure OpenAI — GPT-4.1 mini | **„EU Data Zone Standard"**-Deployment, Region `swedencentral` |
| STT alle Agents | Deepgram Nova-3 | EU-Endpoint `api.eu.deepgram.com` |
| TTS Agent 01 | Cartesia Sonic | Zero-Retention-Mode aktivieren, EU-Hosting (Enterprise) |
| TTS Agent 02+03 | ElevenLabs Flash v2.5 „Johanna" | EU Residency (Enterprise), `enable_logging=False` |
| Kalender | Google Calendar (Service Account) | Workspace-Account in EU-Region |
| Telefonie | Twilio Elastic SIP | EU-Region `de1` (Frankfurt) oder `eu1` (Dublin) |
| LiveKit-Server | self-hosted | VPS in EU |

## Im Detail

### Azure OpenAI

**⚠️ Default ist NICHT DSGVO-konform.** Wenn du bei Azure einen OpenAI-Resource anlegst, steht das Deployment standardmäßig auf „Global Standard" — das bedeutet, Requests können weltweit geroutet werden.

**So richtig machen:**
1. Azure Portal → OpenAI Resource anlegen → Region: **Sweden Central**
2. Im Resource: **Deployments → Create new**
3. Model: `gpt-4.1-mini`
4. **Deployment type: „EU Data Zone Standard"** auswählen (nicht „Global Standard")
5. DPA via Microsoft EU Data Boundary gilt dann

Verifiziere im Azure Portal, dass dein Deployment wirklich „EU Data Zone" zeigt. Alternative neueste Variante ist „Data Zones — EU" je nach UI-Stand bei Microsoft.

### Google Vertex AI (Gemini)

Vertex AI bietet Data Residency in EU, aber der **Gemini 2.5**-Tenant kann laut Google-Doku in manchen Fällen Daten „global für Inference verarbeiten", während nur Storage in EU bleibt. Lese dazu die aktuelle Google-Dokumentation zu AI Data Residency durch.

Für das Tutorial: `europe-west4` setzen und im Video ehrlich adressieren, dass dies der aktuell beste DSGVO-Kompromiss bei Gemini ist, aber keine 100%-EU-Garantie wie bei Azure EU Data Zone.

### Deepgram

Deepgram hat seit 2026 einen dedizierten EU-Endpoint (Frankfurt AWS). URL: `https://api.eu.deepgram.com`. In `.env`:

```
DEEPGRAM_BASE_URL=https://api.eu.deepgram.com
```

Der Agent-Code liest das und übergibt es an den Deepgram-Plugin.

### Cartesia

Cartesia bietet seit 2025 DSGVO-Konformität mit EU-Hosting (Enterprise-Accounts) und Zero-Retention-Mode. In der Cartesia-Konsole unter **Settings → Data Retention → None** aktivieren. DPA unter **Settings → Legal → Request DPA** anfordern.

Wenn dein Account nur Free/Pro ist: Zero-Retention reicht als Setting, aber Hosting bleibt US. Im Video auf diesen Kompromiss hinweisen. Alternative TTS mit voller EU-Garantie: Azure Neural Voices (`de-DE-KatjaNeural`, `de-DE-ConradNeural`).

### ElevenLabs

EU Residency ist ein Enterprise-Feature bei ElevenLabs (Plan-Upgrade nötig). Für Free/Starter: Zero-Retention via `enable_logging=False` aktivieren — reduziert das Risiko, aber die Inference passiert auf US-Infra.

Die „Johanna"-Stimme ist eine Standard-ElevenLabs-Voice, funktioniert in allen Plänen.

### Google Calendar

Siehe `google-calendar-setup.md`. Wichtig: Workspace-Account muss EU-Region haben, sonst läuft dein Kalender auf US-Servern.

### Twilio

Im Twilio-Console unter **Settings → Regions**: **EU1 (Dublin)** oder **DE1 (Frankfurt)** auswählen. DPA im **Privacy Center** unterzeichnen.

Call-Recording ist im Tutorial-Setup aus (würde DSGVO-Fragen bei Kunden-Gesprächen aufwerfen — Consent-Flow, Aufbewahrungsfristen etc.).

## Was tun, wenn ein Provider nicht DSGVO-sauber verfügbar ist?

Im Repo dokumentieren wir bewusst **Alternativen**, wenn die Default-Wahl ein Risiko hat:

| Statt | Nimm |
|---|---|
| Cartesia (falls kein Enterprise) | Azure Neural Voices |
| ElevenLabs (falls kein Enterprise) | Azure Neural Voices |
| Google Vertex AI Gemini (falls Data-Global-Problem) | Azure OpenAI GPT-4.1 mini (EU Data Zone) |
| Deepgram (falls Account nicht auf EU) | Azure Speech STT |
| Google Calendar (ohne Workspace-EU) | Nextcloud Calendar (CalDAV, self-hosted) |

Das Repo ist so aufgebaut, dass du den Provider pro Agent einfach in der Plugin-Zeile tauschen kannst — keine Framework-Änderung nötig.

## Was steht im Video?

Das Tutorial-Video erklärt diese Nuancen **ehrlich** — nicht „LiveKit = automatisch DSGVO", sondern „hier sind die drei Stellschrauben, die du aktiv setzen musst". Das ist der eigentliche Mehrwert gegenüber US-SaaS-Voice-Anbietern: **du entscheidest**, wo deine Daten liegen.
