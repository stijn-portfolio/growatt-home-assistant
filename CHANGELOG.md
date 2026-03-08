# Changelog

Alle belangrijke wijzigingen aan dit project worden gedocumenteerd in dit bestand.

## [1.0.1] - 2025-11-19

### Toegevoegd

- Retry logica voor device turn-on timeouts
  - Configureerbaar aantal pogingen (standaard: 3)
  - Configureerbaar delay tussen pogingen (standaard: 60s)
  - Alleen retry bij timeout errors (code 16)
  - Nieuwe [retry] sectie in config files
- Home Assistant integratie documentatie (SETUP_COMPLETE.md)
- Volledige setup instructies voor Home Assistant OS
- Automation voorbeelden voor periodieke uitvoering

### Gewijzigd

- Windows compatibiliteit verbeterd (Unicode symbolen → ASCII)
- API response handling nu met error code tracking
- Verbeterde logging met retry attempt details
- README.md uitgebreid met setup documentatie link

### Technisch

- `set_device_on_with_retry()` functie toegevoegd
- `_make_request()` retourneert nu ook error codes
- Configureerbare retry parameters via config.ini

## [1.0.0] - 2025-11-19

### Toegevoegd

- Initiële release van Growatt auto-start script
- Automatische detectie van omvormers in "waiting" status
- Automatisch inschakelen via Growatt OpenAPI v4
- Configureerbare actieve uren (standaard 7:00 - 18:00)
- Ondersteuning voor alle Growatt regio's (China, International, North America, Australia)
- Uitgebreide logging naar bestand en console
- Configuratie via INI bestand
- Optie om specifieke devices te targeten
- Automatisch uitsluiten van Noah devices (geen remote control)
- Installatie documentatie voor Raspberry Pi
- Cron job voorbeelden voor automatische uitvoering

### Technisch

- Python 3.7+ compatibiliteit
- Robuuste error handling
- Rate limiting support
- Exit codes voor monitoring
- Configureerbaar via config.ini

## Toekomstige plannen

- [ ] Home Assistant integratie via RESTful sensors
- [ ] Dashboard voor status monitoring
- [ ] Email/push notificaties bij problemen
- [ ] Statistieken en rapportage
- [ ] Docker container voor eenvoudige deployment
- [ ] Meerdere check strategieën (zonlicht-gebaseerd, power-gebaseerd)
