# Growatt Home Assistant automation

![Status](https://img.shields.io/badge/status-production%20ready-brightgreen)
![Python](https://img.shields.io/badge/python-3.7%2B-blue)
![Platform](https://img.shields.io/badge/platform-Home%20Assistant-blue)

Automatische controle voor Growatt zonne-omvormers via Home Assistant.

## Het probleem

Growatt omvormers hebben soms een firmware/hardware fout waardoor ze 's morgens niet automatisch opstarten wanneer er voldoende zonlicht is. Ze blijven hangen in "waiting" status in plaats van automatisch over te schakelen naar "normal" (actief).

## De oplossing

Dit Python script controleert periodiek (bijvoorbeeld elk uur) of je omvormers in "waiting" status staan en zet ze automatisch aan. Het script draait op een Raspberry Pi met Home Assistant en gebruikt de Growatt OpenAPI v4.

## Functionaliteiten

- Controleert automatisch de status van je Growatt omvormers
- Zet omvormers in "waiting" status automatisch aan
- **Intelligente retry logica** - probeert tot 3x bij timeout errors
- Draait alleen overdag (configureerbare tijden)
- Uitgebreide logging voor troubleshooting
- Veilige opslag van API credentials
- Home Assistant automation integratie
- Respecteert API rate limits

## Vereisten

- Raspberry Pi met Home Assistant
- Python 3.7 of hoger
- Growatt API token (zie installatie instructies)
- Netwerktoegang tot Growatt API

## Snelle start

### Voor Home Assistant (aanbevolen)

Volg de stap-voor-stap instructies in **[SETUP_COMPLETE.md](SETUP_COMPLETE.md)** voor een volledige Home Assistant integratie met automation.

### Handmatige installatie

1. Clone deze repository op je Raspberry Pi
2. Installeer dependencies: `pip3 install -r requirements.txt`
3. Kopieer `config.example.ini` naar `config.ini` en vul je gegevens in
4. Test het script: `python3 growatt_auto_start.py`
5. Stel een cron job in voor automatische uitvoering

Zie [INSTALLATION.md](INSTALLATION.md) voor gedetailleerde instructies.

## Gerelateerde projecten

- [Growatt Control App](https://github.com/yourusername/growatt_control_app) - Flutter app voor handmatige controle

## Licentie

MIT

## Bijdragen

Issues en pull requests zijn welkom!
