# Setup Complete - Growatt Home Assistant Integration

Dit document beschrijft hoe het systeem is opgezet en werkt als referentie voor toekomstige configuratie.

## Overzicht

Deze automatisering lost het probleem op van Growatt omvormers die niet automatisch opstarten wanneer er voldoende zonlicht is. Door een firmware/hardware fout blijven ze hangen in "waiting" status in plaats van automatisch over te schakelen naar productie.

## Oplossing

Het systeem controleert automatisch elk uur (tussen configureerbare tijden) of omvormers in "waiting" status staan en schakelt ze automatisch in met intelligente retry logica.

---

## Home Assistant Installatie

### Vereisten

- Home Assistant OS (getest op versie 16.3)
- Advanced SSH & Web Terminal add-on
- Python 3 (komt standaard met HA OS)

### Stap 1: Repository clonen

Via de Web Terminal in Home Assistant:

```bash
cd /config
git clone https://github.com/SDBeu/growatt-homeAssistant.git
cd growatt-homeAssistant
```

### Stap 2: Dependencies installeren

```bash
pip install -r requirements.txt
```

**Opmerking:** De waarschuwing over `root` user is normaal in Home Assistant en kan genegeerd worden.

### Stap 3: Configuratie aanmaken

```bash
cp config.example.ini config.ini
nano config.ini
```

Vul je eigen gegevens in:
- `api_token`: Je 32-karakter Growatt API token
- `region`: Je regio (international, north_america, australia, of china)
- Pas indien gewenst de tijden en retry instellingen aan

**Belangrijke opmerking:** `config.ini` staat in `.gitignore` en wordt NIET naar git gepusht (bevat privégegevens).

### Stap 4: Test het script

```bash
python3 growatt_auto_start.py
```

Je zou output moeten zien zoals:
```
2025-11-19 12:01:14 - INFO - Growatt Auto Start Script v1.0
2025-11-19 12:01:14 - INFO - Starting device check cycle
2025-11-19 12:01:16 - INFO - Found X device(s)
2025-11-19 12:01:16 - INFO - Device: XXXXXX | Status: Normal (1) | Power: XX.XW
```

### Stap 5: Shell command aanmaken

Maak of edit `/config/shell_command.yaml`:

```bash
cd /config
nano shell_command.yaml
```

Voeg toe:
```yaml
growatt_auto_start: "cd /config/growatt-homeAssistant && python3 growatt_auto_start.py"
```

### Stap 6: Configuration.yaml updaten

Edit `/config/configuration.yaml`:

```bash
nano configuration.yaml
```

Voeg deze regel toe (als die er nog niet staat):
```yaml
shell_command: !include shell_command.yaml
```

### Stap 7: Home Assistant herstarten

- Settings → System → Restart
- Wacht tot HA opnieuw opgestart is

### Stap 8: Automation aanmaken

1. Ga naar **Settings** → **Automations & Scenes**
2. Klik **+ Create Automation** → **Create new automation**
3. Schakel over naar **YAML mode** (3 puntjes → Edit in YAML)
4. Plak deze configuratie:

```yaml
alias: Growatt Auto Start
description: Controleert elk uur of omvormers in waiting staan en zet ze aan
triggers:
  - trigger: time_pattern
    hours: /1
    minutes: "0"
conditions:
  - condition: time
    after: "07:00:00"
    before: "18:00:00"
actions:
  - action: shell_command.growatt_auto_start
mode: single
```

5. Sla op en geef een naam (bijv. "Growatt Auto Start")

### Stap 9: Test de automation

- Ga naar de automation
- Klik op de 3 puntjes (⋮) → **Run**
- Check de logs:
  ```bash
  tail -f /config/growatt-homeAssistant/growatt_auto_start.log
  ```

---

## Hoe het werkt

### Dagelijkse cyclus

De automation draait **elk uur** tussen de geconfigureerde tijden (standaard 7:00 - 18:00).

Voor elke run:
1. Script haalt lijst van devices op via Growatt API
2. Checkt status van elk device
3. Als een device in "waiting" (status 0) staat:
   - Stuurt ON commando
   - Bij timeout: wacht 60 seconden en probeert opnieuw
   - Maximaal 3 pogingen
4. Logt resultaten naar `growatt_auto_start.log`

### Retry logica

Het script heeft intelligente retry logica voor timeouts:

```
Poging 1: ON commando → Timeout (code 16)
  ↓ wacht 60 seconden
Poging 2: ON commando → Timeout
  ↓ wacht 60 seconden
Poging 3: ON commando → Succes! ✓
```

**Waarom timeouts?**
- Te weinig zonlicht voor omvormer om te reageren
- Omvormer nog niet responsief
- Normaal gedrag volgens Growatt API documentatie

### Status codes

| Code | Status | Betekenis |
|------|--------|-----------|
| 0 | Waiting | Omvormer wacht op voldoende zonlicht |
| 1 | Normal | Omvormer produceert actief |
| 3 | Fault | Omvormer heeft een fout |

---

## Configuratie opties

### Schedule (wanneer het draait)

```ini
[schedule]
start_hour = 7    # Start om 7:00
end_hour = 18     # Stop om 18:00
```

**Tip:** Pas aan op basis van zonsopgang/zonsondergang in je regio.

### Retry instellingen

```ini
[retry]
max_retries = 3      # Maximaal aantal pogingen
retry_delay = 60     # Seconden tussen pogingen
```

**Belangrijk:** `retry_delay` moet minimaal 60 seconden zijn vanwege API rate limits.

### Device filtering (optioneel)

```ini
[devices]
device_serial_numbers = ABC1234567, DEF9876543
exclude_noah = true
```

Laat `device_serial_numbers` leeg om alle devices te controleren.

---

## Logging

### Log bestand

Locatie: `/config/growatt-homeAssistant/growatt_auto_start.log`

### Logs bekijken

**Live logs volgen:**
```bash
tail -f /config/growatt-homeAssistant/growatt_auto_start.log
```

**Laatste 50 regels:**
```bash
tail -n 50 /config/growatt-homeAssistant/growatt_auto_start.log
```

### Voorbeeld log output

```
2025-11-19 12:13:07 - INFO - Growatt Auto Start Script v1.0
2025-11-19 12:13:07 - INFO - Starting device check cycle
2025-11-19 12:13:09 - INFO - Found 2 device(s)
2025-11-19 12:13:10 - INFO - Device: XXXXXX | Status: Normal (1) | Power: 40.4W
2025-11-19 12:13:10 - INFO - Device: XXXXXX | Status: Waiting (0) | Power: 0.0W
2025-11-19 12:13:10 - INFO -   -> Device is WAITING, attempting to start...
2025-11-19 12:13:10 - INFO -      Attempt 1/3...
2025-11-19 12:13:11 - INFO -   [OK] Successfully sent ON command to XXXXXX
2025-11-19 12:13:11 - INFO - Summary: Checked 2, Found 1 waiting, Started 1, Failed 0
```

---

## Troubleshooting

### Script draait niet automatisch

**Check automation status:**
- Settings → Automations & Scenes
- Zoek je automation
- Controleer of deze aan staat (toggle)

**Check logs voor errors:**
```bash
tail -f /config/growatt-homeAssistant/growatt_auto_start.log
```

### API errors

**Code 16 (PARAMETER_SETTING_RESPONSE_TIMEOUT):**
- Normaal gedrag
- Retry logica handelt dit automatisch af
- Device reageert niet (te weinig zon)

**Code 100-102 (Rate limiting):**
- Te frequent API calls
- Script respecteert rate limits
- Wacht langer tussen handmatige runs

**Code 101 (PERMISSION_DENIED):**
- API token incorrect of verlopen
- Check `config.ini`
- Genereer nieuwe token via Growatt portal

### Device start niet

**Checklist:**
1. Is er voldoende zonlicht?
2. Werkt handmatig starten via de mobiele app?
3. Staat device in "waiting" of in "fault"?
4. Check logs voor exacte foutmelding

**Debug commando:**
```bash
cd /config/growatt-homeAssistant
python3 growatt_auto_start.py
```

### Home Assistant permissions

Als je permission errors krijgt:
```bash
cd /config/growatt-homeAssistant
chmod +x growatt_auto_start.py
```

---

## Onderhoud

### Updates installeren

Wanneer er nieuwe versies beschikbaar zijn:

```bash
cd /config/growatt-homeAssistant
git pull
pip install -r requirements.txt --upgrade
```

### Configuratie wijzigen

```bash
nano /config/growatt-homeAssistant/config.ini
```

Herstart niet nodig - wijzigingen worden bij volgende run gebruikt.

### Automation timing aanpassen

- Settings → Automations & Scenes
- Open je automation
- Pas trigger of condition aan
- Sla op

### Logs opruimen

Handmatig oude logs verwijderen:
```bash
cd /config/growatt-homeAssistant
> growatt_auto_start.log  # Leegt het bestand
```

Of oude logs archiveren:
```bash
mv growatt_auto_start.log growatt_auto_start.log.old
```

---

## Gerelateerde projecten

- **Growatt Control App** - Flutter mobiele app voor handmatige controle
  - Handmatig monitoren en bedienen
  - Real-time status
  - Backup voor wanneer automatisering niet beschikbaar is

---

## Technische details

### API Rate limits (Growatt OpenAPI v4)

| Endpoint | Limit |
|----------|-------|
| queryDeviceList | 1x per 5 seconden |
| queryLastData | 1x per 5 minuten |
| setOnOrOff | 1x per 5 seconden |

### Exit codes

| Code | Betekenis |
|------|-----------|
| 0 | Succesvol (of niets te doen) |
| 1 | Fouten opgetreden |

Gebruik in scripts:
```bash
/config/growatt-homeAssistant/growatt_auto_start.py
if [ $? -eq 0 ]; then
  echo "Success"
fi
```

---

## Toekomstige uitbreidingen

### Notificaties (todo)

Mogelijke integraties:
- Home Assistant mobile app push notificaties
- Persistent notifications in HA
- Email notificaties
- Telegram/WhatsApp berichten

Wanneer notificeren:
- Bij succesvol starten
- Bij mislukte pogingen
- Dagelijkse samenvatting

### Dashboard (todo)

Visualisatie opties:
- Status kaart per omvormer
- Grafiek van dagelijkse starts
- Laatste run tijd en resultaat
- Statistieken (success rate, etc.)

### Geavanceerde logica (todo)

Mogelijke verbeteringen:
- Weersvoorspelling integratie
- Dynamische retry timing op basis van zonkracht
- Statistieken bijhouden
- Seasonal timing adjustment

---

## Support

**Issues of vragen?**
- Open een issue op: https://github.com/SDBeu/growatt-homeAssistant/issues
- Check de documentatie: `README.md`, `INSTALLATION.md`
- Review API reference voor details over error codes

**Handige commando's:**
```bash
# Status check
cd /config/growatt-homeAssistant && python3 growatt_auto_start.py

# Logs bekijken
tail -f /config/growatt-homeAssistant/growatt_auto_start.log

# Configuratie checken
cat /config/growatt-homeAssistant/config.ini
```

---

**Installatie datum:** 19 november 2025
**Versie:** 1.0.1
**Status:** ✅ Productie - Live en werkend
**Platform:** Home Assistant OS 16.3
