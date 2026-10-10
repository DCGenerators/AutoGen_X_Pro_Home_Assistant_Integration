# Home Assistant Core roadmap

HACS is the supported first public channel. Home Assistant Core is a later
milestone and uses the same local controller protocol and permanent AutoGen
device identity.

## Core prerequisites

1. Establish the product and public HACS integration with real users and a stable
   local API.
2. Extract controller communication and data models into a separate open-source
   Python package.
3. Publish that package to PyPI with tagged releases, public CI, tests, and a
   compatible open-source license.
4. Change the integration to depend on the package through `manifest.json`
   instead of owning HTTP transport code.
5. Reach at least Home Assistant's Bronze Integration Quality Scale requirements,
   including full config-flow, setup/unload, discovery, failure, and entity tests.
6. Add Home Assistant documentation and brand submissions.
7. Prepare an initial Core pull request limited to the essential platform and
   features permitted by the current contribution rules.

## Architectural boundary

The future package will own protocol transport, authentication, validated models,
identity checking, and typed controller errors. Home Assistant-specific config
flows, coordinators, devices, and entities remain in the integration.

Cloud fallback is not part of the first Core submission. It can be proposed later
without changing the device-registry identity because local and cloud transports
use the same permanent AutoGen device ID.
