# Hema v1.0.0 (v2026.5.30)

This full local release packages the current Hema/Hermes workspace as version 1.0.0.

## Included

- Updated package metadata to `1.0.0`.
- Included the local user skill set synced into the full package.
- Added PPT workflow skills:
  - `ppt-content-breakdown`
  - `ppt-page-image-grsai`
  - `ppt-image-deck-assembler`
- Added the Grsai-backed PPT image generation workflow and PPT assembly helper scripts.
- Added the PPT workflow architecture document.
- Fixed gateway background message processing so a single inbound platform event is not processed repeatedly when no pending follow-up exists.

## Artifact

Expected full local package:

```text
release/Hema_v-v1.0-hema.local-20260530-offline-full-local.zip
```
