# AutoGen X Pro for Home Assistant

Local monitoring and authenticated control for AutoGen X Pro generator controllers.

> [!IMPORTANT]
> This is a pre-release integration for test controllers. It must not be used to
> control a production generator until the matching firmware and integration have
> completed the hardware safety checklist.

## Goals

- Discover controllers automatically on the local network.
- Configure the integration entirely through the Home Assistant UI.
- Represent each controller as one Home Assistant device.
- Use the permanent AutoGen device ID as the Home Assistant unique ID and serial number.
- Start and stop the generator through the controller's existing state machine and safety checks.
- Preserve the existing AutoGen cloud, mobile app, BLE, local AP, and OTA workflows.
- Prefer local communication, with optional AutoGen cloud fallback in a later release.

## Installation

The public release will be available directly in HACS. During development, add
this repository to HACS as a custom repository with category **Integration**.

After installation:

1. Install the integration through HACS.
2. Restart Home Assistant.
3. Open **Settings > Devices & services**.
4. Select the discovered **AutoGen X Pro**, or select **Add Integration > AutoGen X Pro**.
5. Enter the temporary six-digit code shown by the controller setup page.

No YAML or MQTT broker will be required for the standard setup path.

## Pairing a controller

1. Enable the controller's existing local AP using the AutoGen app/BLE workflow.
2. Join the `AutoGen_Local` Wi-Fi network.
3. Open `http://192.168.4.1:32100/home-assistant`.
4. Select **Generate pairing code**.
5. Return to Home Assistant and enter the code for the discovered controller.

The code expires after ten minutes and can be used once. Home Assistant then
communicates locally with the controller using a revocable high-entropy token.
The permanent AutoGen device ID remains the identity used for support.

## Capabilities

The integration provides battery voltage, charge current, AC voltage,
temperature, controller state, runtime, generator-running, fault, and cloud
connection entities. A generator control switch is created only when firmware
advertises the `start_stop` capability.

The control switch stays on while the controller is starting, running, or in a
start-retry pause. It automatically returns to off when the controller reports
stopped, shutdown/cooldown, fault, standby, post-stop, or a two-wire fault. The
separate **Generator running** entity continues to report the physical run
signal.

A **Reset fault** button is created only when firmware advertises the
`reset_fault` capability. It is available only while the controller reports an
active error, and the controller rejects the command if the error has already
cleared. Reset uses the existing controller error-clear path and never drives a
relay directly.

Every command includes the permanent AutoGen device ID, requires a paired token,
and enters the controller through its existing command/state-machine path. The
Home Assistant integration does not manipulate generator GPIO directly.

## Compatibility

The matching firmware is built as a separate, feature-flagged target. Enabling
Home Assistant does not replace the AutoGen cloud, mobile app, BLE, local AP, or
OTA workflows.

## How the connections coexist

The Home Assistant path is local-first and independent of the existing AutoGen
cloud path:

```text
AutoGen cloud <--- router Wi-Fi <--- controller ---> Home Assistant on the LAN
                                      |
                                      +-- AutoGen_Local access point
                                      |
                                      +-- Bluetooth/mobile app
```

The controller uses ESP32 AP+STA mode while `AutoGen_Local` is enabled. It can
therefore keep its station connection to the router and AutoGen cloud while a
phone is connected to the local access point. Home Assistant polls the
controller directly on the LAN every two seconds so short generator start,
retry, and pause transitions remain visible. The `Cloud connection` entity
reports the controller's existing AutoGen cloud status; Home Assistant traffic
does not pass through that cloud connection.

Cloud fallback for Home Assistant is not included in the local integration. It
requires a separately designed backend authorization contract and will not be
enabled implicitly or by sharing the mobile app's credentials.

## A clean dashboard

Home Assistant integrations provide devices and entities; they do not normally
replace or silently edit a user's dashboard. The automatically generated cards
are functional but deliberately generic.

For a compact AutoGen dashboard:

1. Create a dedicated dashboard and select **Edit dashboard**.
2. Remove the placeholder greeting card and rename `New section` to `Generator`.
3. Add a **Tile** card for `Generator control` and set the card name to
   `Start / stop`.
4. Add compact tiles for `Controller state`, `Fault`, `Generator running`,
   `Battery voltage`, `AC voltage`, and `Cloud connection`.
5. Optionally rename the Home Assistant device to the site's generator name.
   The permanent AutoGen device ID remains unchanged in Device Info and
   diagnostics for support.

The integration supplies translated entity names, device classes, measurement
precision, and icons. Home Assistant combines the device name and entity name in
some automatically generated views; setting a short card name is the standard
way to avoid truncation there.

## Recovery

If a controller's local Home Assistant token is replaced, Home Assistant starts
a reauthentication flow. Generate a new temporary code through
`AutoGen_Local`, enter it in the repair prompt, and the existing device and
entity identities are retained. The integration also provides **Reconfigure**
for manually updating a controller address when automatic Zeroconf discovery is
not available.

## Support

Open a GitHub issue with the Home Assistant diagnostics download and the AutoGen
device ID. Diagnostics redact the local access token. Never post Wi-Fi or cloud
credentials.

## Related firmware

Firmware work is isolated in the separate `AutoGen_X_Pro_Home_Assistant`
project. Production firmware is not modified by this repository.

See [RELEASING.md](RELEASING.md) for the HACS release gates and
[CORE_ROADMAP.md](CORE_ROADMAP.md) for the long-term Home Assistant Core plan.
