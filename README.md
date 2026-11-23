# reefhub ORCA (1. Generation) für Home Assistant

Lokale Steuerung der **reefhub ORCA Controller / ORCAlight Controller** (erste Generation, nicht die Tunze ORCA MK2) über die [lokale API](https://reefhub.de/s/lokale-api/). Kein Cloud-Konto, kein Internet nötig.

**Voraussetzung:** ORCA Controller ab Firmware 7.0.x (Kanal 1–4) bzw. ORCAlight Controller ab 1.2.x (nur Kanal 1). Feste IP im Router empfohlen.

## Installation (HACS)
1. HACS → ⋮ → **Benutzerdefinierte Repositories** → URL dieses Repos, Typ **Integration**
2. **reefhub ORCA** herunterladen, Home Assistant neu starten
3. Einstellungen → Geräte & Dienste → **Integration hinzufügen** → „reefhub ORCA“
4. IP (z. B. `192.168.1.50`) oder `myorca-SERIENNUMMER.local` eintragen

## Entitäten (pro Kanal)
| Entität | Funktion |
|---|---|
| `switch …_kanal_1_drehung` | Drehung an/aus (`/start`, `/stop`) |
| `number …_kanal_1_punkt_a` / `_punkt_b` | Endpunkte −90…90° |
| `number …_kanal_1_geschwindigkeit` | 10…250 |
| `button …_kanal_1_selbsttest` | Kalibrieren (fährt die Endpunkte an) |
| `binary_sensor …_kanal_1_kalibriert` | aus = nach Stromausfall Selbsttest nötig |
| `sensor …_kanal_1_status` / `_selbsttest_status` | Statustext vom Controller |

Dazu: `button …_controller_neu_starten`, `sensor …_cloud_status`, `binary_sensor …_cloud_verbunden`.
Firmware und Seriennummer stehen in den Geräteinfos. Abfrage alle 30 s, nach jedem Befehl sofort.

## Dienst `reefhub_orca.set_channel`
Setzt mehrere Werte auf einmal; nicht angegebene bleiben unverändert.
```yaml
action: reefhub_orca.set_channel
data:
  device_id: <ORCA-Gerät>
  channel: 1
  point_a: -30
  point_b: 30
  speed: 60
```

## Grenzen der lokalen API
Pausen, Sektoren, BOOST, SmartCalibration und Firmware-Updates gibt es nur in der reefhub Web-App. Die API hat kein Passwort – nicht ins Internet freigeben.
