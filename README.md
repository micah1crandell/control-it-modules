# Control-It Community Modules Repository

Official public registry of open-source hardware and software control modules for the [Control-It iOS App](https://github.com/micah1crandell/Control-It).

---

## 📦 What is in this repository?

- **`manifest.json`** — The global index of all verified community modules with versioning and SHA-256 integrity checksums.
- **`modules/`** — Ready-to-use JSON definitions and JavaScript driver scripts for supported hardware & software:
  - **Behringer X32 / M32** (OSC / UDP audio mixing)
  - **Blackmagic ATEM** (Direct UDP switcher control with live tally)
  - **OBS Studio** (OBS WebSocket v5 with scene switching & streaming)
  - **Generic REST / Webhooks** (HTTP/JSON endpoint gateway)
  - **Home Assistant** (Smart home relays & automations)
  - **Philips Hue** (Bridge lighting & entertainment API)
  - **ProPresenter 7** (Presentation software API)
  - **Spotify Player** (Playback & volume control)
  - **VLC Media Player** (HTTP playback control)
  - **vMix Switcher** (TCP/HTTP video production switcher)
  - **Zoom OSC** (Meeting management & audio/video pinning)
- **`MODULE_SDK.md`** — Comprehensive developer guide for creating custom driver scripts using the Control-It Module Runtime.
- **`schemas/module.schema.json`** — Official JSON Schema for validating module files.
- **`templates/`** — Starter templates for building new multi-action modules.
- **`control-it-module.d.ts`** — TypeScript type definitions for driver script authoring.
- **`scripts/validate.py`** — Automated validation script.

---

## 🚀 Creating a New Module

1. **Copy the Template:**
   ```bash
   cp templates/template_multi_action_module.json modules/my_device.json
   ```
2. **Read the SDK Guide:**
   See [`MODULE_SDK.md`](./MODULE_SDK.md) for full documentation on lifecycle hooks, `transport.*` methods, `engine.buffer`, `engine.crypto`, and framing options.
3. **Validate Your Module:**
   ```bash
   python3 scripts/validate.py
   ```
4. **Submit a Pull Request:**
   Submit a PR adding your `modules/my_device.json` and updated `manifest.json`.

---

## 🔒 Integrity & Security

The Control-It iOS app automatically synchronizes modules from this repository, verifying each downloaded file against the published SHA-256 hash in `manifest.json`.
