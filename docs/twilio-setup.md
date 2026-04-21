# Twilio SIP Trunk → LiveKit (einmaliges Setup)

Nur für Agent 3 (Outbound-Calls) nötig. Macht Sinn erst nachdem dein VPS live ist und du eine öffentliche IP hast.

## 1. Twilio-Account vorbereiten

1. Account auf [twilio.com](https://www.twilio.com) erstellen
2. Eine Nummer kaufen: Console → **Phone Numbers → Buy a Number**
   - Voice Capability: Voice ✔
   - Region: am besten DE / AT / CH, oder Länder wo du Anrufer hast
3. Deine **Account SID** und **Auth Token** notieren (Dashboard)

## 2. Elastic SIP Trunk anlegen

1. Console → **Elastic SIP Trunking → Trunks → Create new SIP Trunk**
2. Name: `livekit-tutorial-trunk`
3. Unter **Termination** (Outbound-Calls *von* deinem Agent):
   - Termination URI ist die Domain die Twilio dir zuweist, z. B. `voiceagents-tutorial.pstn.twilio.com`. Diese URI brauchst du für `TWILIO_SIP_TRUNK_URI` in deiner `.env`:
     ```
     TWILIO_SIP_TRUNK_URI=sip:voiceagents-tutorial.pstn.twilio.com
     ```
   - Unter **Authentication** → **Credential Lists** → erstelle eine Credential List mit Username/Passwort. Das sind die Creds, die LiveKit-SIP bei Twilio nutzt.
     ```
     TWILIO_ACCOUNT_SID=<credential-list-username>
     TWILIO_AUTH_TOKEN=<credential-list-passwort>
     ```
     *(Verwende NICHT den Twilio Account-Auth-Token hier, sondern die Trunk-Credentials!)*
4. Unter **Origination** (Inbound-Calls *zu* deinem Agent — optional, nicht im Tutorial-Scope):
   - Origination URI: `sip:<vps-ip>:5060;transport=udp`
5. Unter **Numbers**: klicke **Add a Number** und ordne deine gekaufte Nummer zu.

## 3. `.env` auf dem VPS füllen

```bash
TWILIO_SIP_TRUNK_URI=sip:voiceagents-tutorial.pstn.twilio.com
TWILIO_ACCOUNT_SID=<trunk-credential-user>
TWILIO_AUTH_TOKEN=<trunk-credential-pw>
TWILIO_PHONE_NUMBER=+491701234567   # deine Twilio-Nummer, E.164
```

## 4. LiveKit Outbound-Trunk erzeugen

Auf dem VPS:

```bash
cd /opt/livekit-voice-agents-de
python3 -m pip install livekit python-dotenv
python3 scripts/setup-sip.py
```

Output:
```
✓ Outbound SIP Trunk erstellt.

Bitte in deiner .env eintragen:
LIVEKIT_OUTBOUND_TRUNK_ID=ST_abc123...
```

Diese ID in `.env` eintragen, dann Frontend neu starten:
```bash
docker compose up -d --force-recreate frontend
```

## 5. Test

Im Browser: `https://voice.meine-domain.de/outbound` → Formular ausfüllen mit deiner echten Handy-Nummer → Submit → dein Handy sollte in wenigen Sekunden klingeln.

Im Live-Transkript auf der Seite siehst du, was der Agent und du gerade sagt. Am Ende erscheint das qualifizierte Lead-JSON.

## Fehlerdiagnose

**Handy klingelt nicht:**
- Twilio Console → **Monitor → SIP Logs** checken. Siehst du den Outbound-Versuch?
- LiveKit-SIP-Logs: `docker compose logs livekit-sip`
- Firewall: sind UDP 5060 und 10000–20000 offen?

**Anrufer hört keinen Ton / Agent hört nichts:**
- RTP-Ports (10000–20000/UDP) geöffnet?
- NAT-Probleme: auf VPS sollte Public-IP direkt auf eth0 sein (nicht NAT). Bei NAT-VPS: `external_ip` in `livekit-sip.yaml` konfigurieren.

**„Authentication failed":**
- Du verwendest Account-SID/Auth-Token statt Trunk-Credential-List-Username/Password. Unterscheiden — siehe Schritt 2.3.

## DSGVO

- Twilio Frankfurt / Dublin als Rechenzentrum wählen: Console → Regions → `eu1` (Dublin) oder `de1` (Frankfurt).
- DPA (Data Processing Addendum) im Twilio-Dashboard unter **Privacy & Compliance** unterzeichnen.
- Kein Call-Recording aktivieren (Tutorial-Setup macht das standardmäßig nicht).
