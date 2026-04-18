# Installatie instructies

Stap-voor-stap gids om het Growatt auto-start script op je Raspberry Pi te installeren.

## Vereisten

- Raspberry Pi met Raspberry Pi OS (of andere Linux distributie)
- Python 3.7 of hoger
- Internettoegang
- Growatt API token

## Stap 1: API token verkrijgen

1. Ga naar de Growatt OpenAPI website voor jouw regio:
   - International (Europa): https://openapi.growatt.com
   - North America: https://openapi-us.growatt.com
   - Australia/NZ: https://openapi-au.growatt.com
   - China: https://openapi-cn.growatt.com

2. Log in met je Growatt account
3. Ga naar **API Management** → **Create API Account**
4. Noteer je **API token** (32 karakters)
5. Bewaar deze veilig - je hebt hem zo nodig

## Stap 2: project installeren op Raspberry Pi

### SSH verbinding maken

```bash
ssh pi@raspberrypi.local
# of: ssh pi@<IP_ADRES>
```

### Repository clonen

```bash
# Navigeer naar een geschikte locatie
cd ~

# Clone de repository (vervang URL met je eigen git URL)
git clone https://github.com/jouwgebruikersnaam/growatt-homeAssistant.git

# Ga naar de project directory
cd growatt-homeAssistant
```

**Nog geen git repository?** Kopieer dan de bestanden handmatig:

```bash
# Maak directory aan
mkdir ~/growatt-homeAssistant
cd ~/growatt-homeAssistant

# Kopieer bestanden van je computer via SCP of gebruik nano om ze te maken
```

## Stap 3: Python dependencies installeren

```bash
# Update package manager
sudo apt update

# Installeer pip als je het nog niet hebt
sudo apt install python3-pip -y

# Installeer dependencies
pip3 install -r requirements.txt
```

## Stap 4: configuratie instellen

```bash
# Kopieer het voorbeeld config bestand
cp config.example.ini config.ini

# Bewerk de configuratie
nano config.ini
```

Vul de volgende gegevens in:

```ini
[growatt]
api_token = JOUW_32_KARAKTER_TOKEN_HIER
region = international  # Of jouw regio

[schedule]
start_hour = 7   # Start controle om 7:00
end_hour = 18    # Stop controle om 18:00

[devices]
device_serial_numbers =  # Laat leeg voor alle devices
exclude_noah = true
```

Opslaan: `Ctrl+X`, dan `Y`, dan `Enter`

## Stap 5: script testen

### Handmatig uitvoeren

```bash
python3 growatt_auto_start.py
```

Je zou output moeten zien zoals:

```
2025-01-19 10:30:15 - INFO - Growatt Auto Start Script v1.0
2025-01-19 10:30:15 - INFO - ============================================================
2025-01-19 10:30:15 - INFO - Starting device check cycle
2025-01-19 10:30:16 - INFO - Found 2 device(s)
2025-01-19 10:30:17 - INFO - Device: Omvormer 1 | Status: Waiting (0) | Power: 0W
2025-01-19 10:30:17 - INFO -   → Device is WAITING, attempting to start...
2025-01-19 10:30:18 - INFO -   ✓ Successfully sent ON command to Omvormer 1
2025-01-19 10:30:19 - INFO - Summary: Checked 2 device(s), Found 1 waiting, Started 1, Failed 0
2025-01-19 10:30:19 - INFO - ============================================================
```

### Logs bekijken

```bash
# Bekijk het log bestand
cat growatt_auto_start.log

# Of volg het live
tail -f growatt_auto_start.log
```

## Stap 6: automatisch uitvoeren met cron

### Crontab bewerken

```bash
crontab -e
```

Als dit de eerste keer is, kies een editor (bijvoorbeeld `nano` = optie 1).

### Cron job toevoegen

Voeg de volgende regel toe aan het einde van het bestand:

**Optie A: Elk uur tussen 7:00 - 18:00**

```bash
0 7-18 * * * cd ~/growatt-homeAssistant && /usr/bin/python3 growatt_auto_start.py >> ~/growatt-homeAssistant/cron.log 2>&1
```

**Optie B: Elke 30 minuten tussen 7:00 - 18:00**

```bash
*/30 7-18 * * * cd ~/growatt-homeAssistant && /usr/bin/python3 growatt_auto_start.py >> ~/growatt-homeAssistant/cron.log 2>&1
```

**Optie C: Specifieke tijden (bijv. 7:00, 9:00, 11:00, 13:00, 15:00, 17:00)**

```bash
0 7,9,11,13,15,17 * * * cd ~/growatt-homeAssistant && /usr/bin/python3 growatt_auto_start.py >> ~/growatt-homeAssistant/cron.log 2>&1
```

Opslaan: `Ctrl+X`, dan `Y`, dan `Enter`

### Cron job verificeren

```bash
# Bekijk je actieve cron jobs
crontab -l
```

## Stap 7: verificatie

### Wacht tot de volgende geplande tijd

Of test direct door de cron tijd aan te passen naar een paar minuten in de toekomst.

### Check de logs

```bash
# Script log
tail -f ~/growatt-homeAssistant/growatt_auto_start.log

# Cron log
tail -f ~/growatt-homeAssistant/cron.log
```

## Troubleshooting

### Script draait niet

**Check of cron service actief is:**

```bash
sudo systemctl status cron
```

**Handmatig draaien om errors te zien:**

```bash
cd ~/growatt-homeAssistant
python3 growatt_auto_start.py
```

### API errors

**"Invalid token" of authentication errors:**
- Controleer of je token correct is in `config.ini`
- Controleer of je de juiste regio hebt ingesteld
- Test je token in de Flutter app

**Rate limit errors (code 100-102):**
- Verminder de frequentie in crontab
- Wacht 5-10 minuten en probeer opnieuw

### Geen devices gevonden

```bash
# Check of API verbinding werkt
python3 -c "
from growatt_auto_start import GrowattAPI
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

api = GrowattAPI(config['growatt']['api_token'], config['growatt']['region'])
devices = api.get_device_list()
print(f'Found {len(devices)} devices')
for d in devices:
    print(f\"  - {d['deviceSn']} ({d['deviceType']})\")
"
```

### Permissions problemen

```bash
# Maak script executable
chmod +x growatt_auto_start.py

# Check file permissions
ls -la growatt_auto_start.py config.ini
```

## Geavanceerde opties

### Email notificaties bij errors

Voeg dit toe aan je crontab regel:

```bash
0 7-18 * * * cd ~/growatt-homeAssistant && /usr/bin/python3 growatt_auto_start.py || echo "Growatt script failed" | mail -s "Growatt Error" jouw@email.com
```

### Systemd service (alternatief voor cron)

Maak een systemd timer voor meer controle. Zie de systemd documentation voor details.

## Onderhoud

### Logs opruimen

```bash
# Logs ouder dan 30 dagen verwijderen
find ~/growatt-homeAssistant -name "*.log" -mtime +30 -delete
```

### Updates installeren

```bash
cd ~/growatt-homeAssistant
git pull
pip3 install -r requirements.txt --upgrade
```

## Volgende stappen

- Test gedurende een paar dagen
- Monitor de logs regelmatig
- Pas de timing aan op basis van je ervaring
- Overweeg Home Assistant integratie voor dashboard visualisatie

## Hulp nodig?

Open een issue op GitHub of raadpleeg de documentatie.
