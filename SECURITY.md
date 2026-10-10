# Security policy

Do not report security vulnerabilities in public issues. Contact DC Generators
through its private support channel and include the affected firmware version,
integration version, and AutoGen device ID.

Never include pairing codes, bearer tokens, Wi-Fi credentials, cloud credentials,
or unredacted Home Assistant storage in a report. Home Assistant diagnostics from
this integration redact the local bearer token.

Pairing must be deliberately opened through the controller's local AP and is
time-limited and single-use. Re-pairing replaces the previously authorized Home
Assistant token without changing other AutoGen connection methods.
