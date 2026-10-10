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

Every command includes the permanent AutoGen device ID, requires a paired token,
and enters the controller through its existing command/state-machine path. The
Home Assistant integration does not manipulate generator GPIO directly.

## Compatibility

The matching firmware is built as a separate, feature-flagged target. Enabling
Home Assistant does not replace the AutoGen cloud, mobile app, BLE, local AP, or
OTA workflows.

## Support

Open a GitHub issue with the Home Assistant diagnostics download and the AutoGen
device ID. Diagnostics redact the local access token. Never post Wi-Fi or cloud
credentials.

## Related firmware

Firmware work is isolated in the separate `AutoGen_X_Pro_Home_Assistant`
project. Production firmware is not modified by this repository.

See [RELEASING.md](RELEASING.md) for the HACS release gates and
[CORE_ROADMAP.md](CORE_ROADMAP.md) for the long-term Home Assistant Core plan.
