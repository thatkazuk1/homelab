# Operations: Home Assistant — Tuya sensors that the official integration can't read

Some cheap Tuya devices are recognised by Home Assistant's official Tuya integration (entities
get created) but never report a value — every reading stays `unknown`, even though the Smart
Life app shows live data. This is the workaround the homelab uses: poll the **Tuya IoT
Platform** cloud API directly from a `command_line` sensor.

Currently applies to:

| Device | Product ID | Symptom |
|---|---|---|
| 4× "T & H Sensor" (temp/humidity) | `xeagimantb7d7apb` | mis-categorised `tdq`; no MQTT push; `status: {}` from the sharing SDK. Upstream: [home-assistant/core#163947](https://github.com/home-assistant/core/issues/163947) |
| 7× T34 Smart Plug (energy total) | various | report live watts but the kWh counter is stuck at 0; only `add_ele` (an unusable increment) is exposed |

The plugs' **live power (W)** works fine through the official integration — only their
cumulative energy is broken, and that's solved separately with Riemann-sum sensors (below).

## Why the official integration fails

HA's `tuya` integration (the `tuya-device-sharing-sdk`, app-account-linked) gets device status
from an MQTT push. For these products the device never pushes, and the initial status fetch
returns an empty object. A `tuya-device-handlers` quirk hardcodes the datapoints so entities
appear, but there is nothing to populate them. The **IoT Platform OpenAPI**
(`/v2.0/cloud/thing/{id}/shadow/properties`) *does* return the values — it's a different backend.

## One-time: Tuya IoT Platform Cloud Project

1. Create an account at <https://iot.tuya.com>.
2. **Cloud → Development → Create Cloud Project**
   - Development Method: **Smart Home**
   - **Data Center: must match the app account.** Check an existing HA Tuya device's
     diagnostics for the `endpoint` (`apigw.tuyaeu.com` → Central Europe). Wrong DC = nothing works.
3. Copy the **Access ID** and **Access Secret** from the project Overview page.
4. **Devices → Link App Account → Add App Account** → scan the QR with the Smart Life app.
   All homes/devices now appear under the project.
5. **Service API → Go to Authorize** → ensure **IoT Core** + **Authorization Token Management**
   are subscribed (renew the free trial if expired).
6. Verify: **Cloud → API Explorer → IoT Core → Query Properties**, enter a device ID, Submit.
   A non-empty `result.properties` array confirms it works.

## Home Assistant side (host `core-01`, HA container)

### Credentials

```json
// /opt/homelab/homeassistant/config/scripts/.tuya_cloud.json   (chmod 600, root:root)
{"region": "eu", "access_id": "<ACCESS_ID>", "access_secret": "<ACCESS_SECRET>"}
```

### Poller script

`config/scripts/tuya_cloud_th.py` — stdlib-only Tuya OpenAPI client (HMAC-SHA256 signing),
retries + token-cache recovery, caches the token and per-device properties under `/tmp`
(120 s TTL) so a batch of `command_line` sensors costs ~1 token + N property calls.

```
Usage: tuya_cloud_th.py <device_id> <temp|humidity|battery|raw>
```

Device IDs come from the IoT Platform Devices list (or an HA Tuya device's diagnostics `id`).

### `command_line` sensors (`configuration.yaml`)

One per reading. `scan_interval: 900` for temp/humidity, `3600` for battery.

```yaml
command_line:
  - sensor:
      name: "Living Room Temperature"
      unique_id: tuya_cloud_living_room_temperature
      command: "python3 /config/scripts/tuya_cloud_th.py <device_id> temp"
      command_timeout: 25
      unit_of_measurement: "°C"
      device_class: temperature
      state_class: measurement
      availability: "{{ value not in ['unknown', 'unavailable', ''] }}"
      scan_interval: 900
```

`battery` returns an enum (`low`/`middle`/`high`); a `template` `binary_sensor` ORs the four
into `binary_sensor.t_h_sensor_battery_low`, and an automation notifies on it.

### Riemann energy sensors (`configuration.yaml`)

For plugs that report watts but not kWh. One `integration` sensor per plug:

```yaml
sensor:
  - platform: integration
    source: sensor.t34_smart_plug_2_tv_power
    name: "TV Energy"
    unique_id: riemann_tv_energy
    unit_prefix: k
    unit_time: h
    method: left
    max_sub_interval: "00:01:00"
    round: 3
```

These feed the **Energy dashboard** `device_consumption` list (Settings → Dashboards → Energy,
or `.storage/energy` via the `energy/save_prefs` websocket call). They start from 0 (no
back-history) and drift ~2–4 % vs a real meter.

## Moving this to another host

Everything is host-local (HA config is not in git). To reproduce elsewhere:

1. Copy `config/scripts/tuya_cloud_th.py` and create `.tuya_cloud.json` with the same
   Access ID/Secret (the one Cloud Project covers the whole Smart Life account — no need for a
   new project).
2. Re-create the `command_line` / `sensor: integration` blocks in that instance's
   `configuration.yaml` with the same device IDs.
3. If the new instance is in a different data center region, set `region` accordingly and
   confirm the Cloud Project's DC matches.

## Long-term

The real fix is different hardware: a `wsdcg`-category Tuya T&H sensor (works natively), or
Zigbee sensors via ZHA/Zigbee2MQTT with a local coordinator — no cloud dependency. See the
project notes for the hardware options.
