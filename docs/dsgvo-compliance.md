# DSGVO-Konformität — Provider-Übersicht

Dieses Repo ist darauf ausgelegt, nur mit EU-Region-Endpoints oder Zero-Retention-Modes zu arbeiten. Kein Provider ist „automatisch" DSGVO-konform — du musst aktiv die richtige Region / das richtige Deployment konfigurieren. Diese Seite listet auf, worauf du pro Provider achten musst.

## Übersicht

| Komponente | Provider | DSGVO-Konfiguration |
|---|---|---|
| Realtime-Modell Agent 01 | Google Vertex AI — Gemini 2.5 Flash Native Audio | `europe-west4` (Niederlande) oder unterstützte EU-Region |
| LLM Agent 02+03 | Google Vertex AI — Gemini 2.5 Flash | `europe-west4` (Niederlande) oder unterstützte EU-Region |
| STT alle Agents | Azure Speech | Speech-Resource in EU-Region, z. B. `germanywestcentral`, `westeurope`, `swedencentral` |
| TTS alle Agents | Azure Speech Neural Voices | Speech-Resource in EU-Region, z. B. `de-DE-SeraphinaMultilingualNeural` |
| Kalender | Google Calendar (Service Account) | Workspace-Account in EU-Region |
| Telefonie | Twilio Elastic SIP | EU-Region `de1` (Frankfurt) oder `eu1` (Dublin) |
| LiveKit-Server | self-hosted | VPS in EU |

## Im Detail

### Google Vertex AI (Gemini)

Vertex AI ist der Default-LLM-Stack in diesem Repo. Für Agent 01 nutzen wir `gemini-2.5-flash-lite`, für Tool-Calling in Agent 02/03 `gemini-2.5-flash`.

Für das Tutorial: `europe-west4` setzen. Google dokumentiert für Vertex AI Data Residency, dass ML Processing in der spezifischen Region oder Multi-Region des Requests stattfindet, sofern Modell und Capability Data Residency unterstützen. Bei Gemini 2.5 Flash/Flash-Lite ist Europa als ML-Processing-Multi-Region dokumentiert.

### Azure Speech

Azure Speech ist die Default-Wahl in diesem Repo, weil STT und TTS über denselben Microsoft-DPA/EU-Region-Stack laufen können. Lege die Speech-Resource in einer EU-Region nahe am Server an, z. B. `germanywestcentral`, `westeurope`, `swedencentral` oder `francecentral`.

In `.env`:

```
AZURE_SPEECH_KEY=<key>
AZURE_SPEECH_REGION=germanywestcentral
AZURE_SPEECH_LANGUAGE=de-DE
AZURE_SPEECH_VOICE=de-DE-SeraphinaMultilingualNeural
```

Gute deutsche Stimmen zum Testen:

| Voice | Typ |
|---|---|
| `de-DE-SeraphinaMultilingualNeural` | weiblich, modern, natürlich |
| `de-DE-FlorianMultilingualNeural` | männlich, modern, natürlich |
| `de-DE-KatjaNeural` | weiblich, stabiler Standard |
| `de-DE-ConradNeural` | männlich, stabiler Standard |
| `de-DE-KlarissaNeural` | weiblich, Alternative |

### Deepgram als Alternative

Deepgram stellt einen dedizierten EU-Endpoint bereit. URL: `https://api.eu.deepgram.com`. In `.env`:

```
DEEPGRAM_BASE_URL=https://api.eu.deepgram.com
DEEPGRAM_MODEL=nova-3
DEEPGRAM_LANGUAGE=de
```

Der Default-Code nutzt Azure Speech. Deepgram bleibt eine optionale Latenz-Alternative. Für rein deutsche Gespräche ist `language=de` am stabilsten. Für Code-Switching oder internationale Demos kannst du `DEEPGRAM_LANGUAGE=multi` verwenden; Nova-3 Multilingual unterstützt u. a. Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch, Portugiesisch, Hindi, Japanisch und Russisch in Echtzeit.

Für Produktion: DPA/AVV abschließen und sicherstellen, dass keine Teilnahme am Model Improvement Partnership Program vereinbart ist, wenn Kundendaten nicht fürs Training genutzt werden sollen.

### Cartesia als Alternative

Cartesia kann für natürlichere Stimmen interessant sein, sollte im DSGVO-Tutorial aber nur als Enterprise-/Custom-Vertragsoption genannt werden. Zero-Retention muss im Account aktiviert und über DPA/Vertrag abgesichert sein. EU-Hosting nicht einfach voraussetzen, sondern schriftlich oder im Account bestätigen lassen.

Wenn dein Account nur Free/Pro ist: nicht als EU-only Default verkaufen. Dafür nutzt dieses Repo Azure Speech als Standard.

### ElevenLabs als Alternative

EU Residency ist ein Enterprise-Feature bei ElevenLabs. Dafür gibt es ein isoliertes EU-Environment mit eigener API-URL (`https://api.eu.residency.elevenlabs.io`) und eigenem API-Key. Zero-Retention ist zusätzlich zu aktivieren und nicht automatisch durch EU Residency eingeschaltet.

Für Free/Starter/Creator nicht als EU-only Default verkaufen. Das LiveKit-Plugin kann technisch eine `base_url` bekommen, aber ohne freigeschalteten EU-Enterprise-Workspace bleibt es beim normalen ElevenLabs-Setup.

### Google Calendar

Siehe `google-calendar-setup.md`. Wichtig: Workspace-Account muss EU-Region haben, sonst läuft dein Kalender auf US-Servern.

### Twilio

Im Twilio-Console unter **Settings → Regions**: **EU1 (Dublin)** oder **DE1 (Frankfurt)** auswählen. DPA im **Privacy Center** unterzeichnen.

Call-Recording ist im Tutorial-Setup aus (würde DSGVO-Fragen bei Kunden-Gesprächen aufwerfen — Consent-Flow, Aufbewahrungsfristen etc.).

## Was tun, wenn ein Provider nicht DSGVO-sauber verfügbar ist?

Im Repo dokumentieren wir bewusst **Alternativen**, wenn die Default-Wahl ein Risiko hat:

| Statt | Nimm |
|---|---|
| Cartesia / ElevenLabs ohne Enterprise-EU | Azure Speech Neural Voices |
| Vertex AI Modell in gewählter EU-Region nicht verfügbar | anderes Vertex-Gemini-Modell in unterstützter EU-Region |
| Deepgram ohne DPA/EU-Endpoint | Azure Speech STT |
| Google Calendar (ohne Workspace-EU) | Nextcloud Calendar (CalDAV, self-hosted) |

Das Repo ist so aufgebaut, dass du den Provider pro Agent einfach in der Plugin-Zeile tauschen kannst — keine Framework-Änderung nötig.

## Was steht im Video?

Das Tutorial-Video erklärt diese Nuancen **ehrlich** — nicht „LiveKit = automatisch DSGVO", sondern „hier sind die drei Stellschrauben, die du aktiv setzen musst". Das ist der eigentliche Mehrwert gegenüber US-SaaS-Voice-Anbietern: **du entscheidest**, wo deine Daten liegen.
