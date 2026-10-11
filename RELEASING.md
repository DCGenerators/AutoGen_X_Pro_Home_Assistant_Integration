# Public release checklist

## HACS release gate

- [x] One integration in the repository under `custom_components/autogen_x_pro`.
- [x] UI config flow and Zeroconf discovery; no YAML setup required.
- [x] Permanent AutoGen device ID used for config, device, entity, and command identity.
- [x] Local pairing token is redacted from diagnostics.
- [x] HACS and hassfest GitHub validation workflows are present.
- [x] Local brand icons are included for supported Home Assistant versions.
- [x] Validate the integration against the controller simulator.
- [x] Flash only the isolated `esp32dev_home_assistant` target to a test controller.
- [ ] Complete every item in the firmware bench-test checklist.
- [ ] Install through HACS on a clean Home Assistant system.
- [ ] Verify Zeroconf discovery, pairing, reload, restart, IP change, and removal.
- [ ] Verify monitoring while AutoGen cloud, mobile app, BLE, and local AP remain operational.
- [ ] Verify accepted and safely rejected start/stop commands on a test rig.
- [x] Choose and add the public open-source license.
- [x] Publish the GitHub repository and enable Issues.
- [x] Add repository description and topics: `home-assistant`, `hacs`, `autogen-x-pro`.
- [x] Publish a SemVer GitHub pre-release from an immutable tag.
- [ ] Add the brand to `home-assistant/brands` if required by current HACS validation.
- [ ] Submit the integration to the HACS default repository and address review feedback.

The first public tag should remain a pre-release until the real-controller and
clean-install tests pass. Do not publish a release that can control a generator
based only on simulator results.

## Release versioning

Use semantic versions. The integration manifest version, Git tag, and GitHub
release version must match. Start with `0.1.0` for the first tested pre-release.

## Rollback

Keep the previous GitHub release available. A user can select that version in
HACS without changing controller firmware, its AutoGen device ID, or any AutoGen
cloud/mobile configuration.
