# Control-It Community Modules Repository

Official public registry and developer SDK of open-source hardware and software control modules for the Control-It application on iOS, iPadOS, and macOS.

Unlike legacy control platforms that require an external host computer running a Node.js server, Control-It runs autonomously on Apple devices. Modules are standalone, portable JSON drivers executed by an embedded JavaScriptCore runtime (`ModuleRuntimeEnvironment`) with native, low-latency TCP, UDP, WebSocket, HTTP, and OSC networking.

---

## Architecture Overview

Control-It operates on a two-repository architecture:

1. **Control-It (Main Application)**: The private core native iOS and macOS application engine, user interface, CoreData/CloudKit synchronization layer, and embedded HTTP/Bonjour trigger server.
2. **control-it-modules (This Repository)**: The canonical public registry, agent skills pack, schema definitions, and headless test harness.

### Over-The-Air (OTA) Synchronization

When Control-It is launched on a device:
- The app checks `manifest.json` on a 24-hour cooldown cycle via GitHub CDN (`https://raw.githubusercontent.com/micah1crandell/control-it-modules/main/manifest.json`).
- If an update is detected, the app downloads new and updated module files into its local cache (`Application Support/CommunityModules/`).
- Every downloaded module is verified against the cryptographically secure SHA-256 hash published in `manifest.json`.
- If offline, the application falls back to its bundled snapshot.
- Custom modules authored locally or hot-deployed over Wi-Fi always take priority over public community modules with identical IDs.

---

## Repository Structure

```
control-it-modules/
|-- manifest.json                   # Global registry index with versions and SHA-256 hashes
|-- control-it-module.d.ts          # TypeScript type definitions for driver script authoring
|-- SKILL.md                        # Master AI Agent instruction pack for building modules
|-- SPECIFICATION.md                # Comprehensive JSON schema specification and field rules
|-- DRIVER_RUNTIME_REFERENCE.md     # JavaScript driver runtime API and sandbox documentation
|-- PROTOCOL_PLAYBOOKS.md           # Implementation playbooks for TCP, UDP, WebSocket, HTTP, OSC
|-- MIGRATING_FROM_COMPANION.md     # Complete Bitfocus Companion migration guide
|-- modules/                        # Canonical, verified hardware and software module files
|   |-- behringer_x32.json
|   |-- blackmagic_atem.json
|   |-- generic_rest_api.json
|   |-- home_assistant.json
|   |-- obs_studio.json
|   |-- philips_hue.json
|   |-- propresenter_7.json
|   |-- propresenter_http.json
|   |-- spotify_player.json
|   |-- vlc_media_player.json
|   |-- vmix_switcher.json
|   |-- zoom_osc.json
|-- schemas/
|   `-- module.schema.json          # Formal JSON Schema definition
|-- templates/                      # Boilerplate templates for rapid driver creation
|   |-- template_rest_bearer_polling.json
|   |-- template_tcp_linedelimited.json
|   |-- template_udp_binary.json
|   |-- template_websocket_jsonrpc.json
|   |-- template_multi_action_module.json
|   |-- template_pjlink_projector.json
|   `-- template_visca_over_ip.json
`-- scripts/
    |-- validate.py                 # Repository validation and SHA-256 hash check
    |-- test_module.py              # Headless JavaScriptCore driver runner and mock harness
    `-- control_it_mcp.py           # Wi-Fi Developer Bridge CLI tool and MCP Server
```

---

## Building Modules with AI Coding Agents

This repository is optimized for autonomous and pair-programming workflows with AI coding assistants (Google Antigravity, Cursor, Claude Code, GitHub Copilot, ChatGPT, or Claude Desktop).

### Pointing an AI Agent at the Skills Pack

When initiating a task with an AI coding agent, direct it to read `SKILL.md`:

```
Read SKILL.md in this repository. Follow all instructions and schemas to build a Control-It module for [Hardware Device or Software Name] using [Protocol: TCP, UDP, WebSocket, HTTP, or OSC].
```

The agent will automatically:
1. Review `SPECIFICATION.md` for JSON schema compliance.
2. Consult `PROTOCOL_PLAYBOOKS.md` for protocol-specific framing and state patterns.
3. Review `DRIVER_RUNTIME_REFERENCE.md` for APIs (`engine.setVariable`, `engine.crypto`, `engine.binary`, `engine.osc`, Node `Buffer`).
4. Generate the complete JSON module with CommonJS driver script.
5. Run `python3 scripts/test_module.py` to test and verify the driver headlessly.
6. Hot-deploy and test the module directly on your physical device over Wi-Fi using `control_it_mcp.py`.

---

## Developer Wi-Fi Bridge and MCP Server

Control-It includes an embedded HTTP and Server-Sent Events (SSE) server that allows external developer tools and AI agents to communicate directly with an iOS, iPadOS, or macOS device on the local network.

### 1. Enabling the Bridge on Your Device

1. Open **Control-It** on your iPhone, iPad, or Mac.
2. Ensure the device is connected to the same local Wi-Fi network as your computer.
3. Go to **Community Hub** and select the **Agent & Wi-Fi Dev Bridge** card, or open **Settings -> Trigger Server & Remote API**.
4. Turn on the server. The card displays your active IP address and port (default: `8080`).

### 2. Command-Line Interface (CLI)

The script `scripts/control_it_mcp.py` operates without external dependencies (pure Python 3 standard library). It automatically discovers running Control-It instances on your local subnet using Bonjour mDNS (`_controlit-dev._tcp`), or accepts explicit `--host` and `--port` parameters.

#### Device Status and Health Check
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 status
```
Output:
```json
{
  "app": "Control-It",
  "deviceName": "iPad Pro",
  "systemName": "iPadOS",
  "systemVersion": "18.2",
  "sdkVersion": "2.2.0",
  "installedModulesCount": 14,
  "activeConnectionsCount": 3
}
```

#### List Installed Modules
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 list-modules
```

#### Hot-Deploy a Module Over Wi-Fi
Instantly uploads and activates a driver JSON file in the app sandbox without restarting the app:
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 deploy modules/my_device.json
```

#### Test Action Execution Remotely
Executes an action in the app driver runtime, measures execution latency, and returns console logs and mutated state variables:
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 test-action my_device power_on --params '{"zone":"main"}'
```

#### Inject Simulated Hardware Telemetry
Injects simulated binary, hex, or JSON packets directly into the driver's `onMessage` handler to verify response parsing and variable extraction without physical hardware:
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 simulate-packet my_device --text '{"status":"ready","slide_index":4}'
```

#### Query Active State Variables
Inspects the live state of all dynamic variables currently stored by the driver:
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 variables my_device
```

#### Export Module JSON from Device
Exports the active JSON definition of any module currently installed on the device:
```bash
python3 scripts/control_it_mcp.py --host 192.168.1.50 get-module my_device > exported_module.json
```

### 3. Model Context Protocol (MCP) Server Setup

`scripts/control_it_mcp.py` implements the standard Model Context Protocol (MCP) stdio specification, exposing 6 native tools to AI agents:
- `control_it_status`: Check connection state and device environment.
- `control_it_list_modules`: List all modules on device.
- `control_it_get_module`: Fetch full JSON specification for an installed module.
- `control_it_deploy_module`: Hot-deploy a module definition to the active device.
- `control_it_test_action`: Execute an action and capture execution output and logs.
- `control_it_simulate_packet`: Inject simulated hardware telemetry and observe variable changes.

#### Configuration for Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "control-it": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/control-it-modules/scripts/control_it_mcp.py",
        "--host", "192.168.1.50",
        "--port", "8080"
      ]
    }
  }
}
```

#### Configuration for Cursor (`~/.cursor/mcp.json`) or Antigravity (`mcp_config.json`)
```json
{
  "mcpServers": {
    "control-it": {
      "command": "python3",
      "args": [
        "/ABSOLUTE/PATH/TO/control-it-modules/scripts/control_it_mcp.py"
      ]
    }
  }
}
```
*(If `--host` is omitted, the script automatically resolves the target device via Bonjour mDNS).*

---

## Headless Driver Testing (`scripts/test_module.py`)

You can test JavaScript driver syntax, lifecycle hooks, network packet serialization, and variable mutations without requiring a physical device or running app.

`scripts/test_module.py` runs on macOS using the built-in JavaScriptCore framework via PyObjC (preinstalled on macOS) or falls back to Node.js / Python mock runners:

```bash
# Run full automated test suite on a module
python3 scripts/test_module.py modules/propresenter_http.json

# Test a specific action
python3 scripts/test_module.py modules/propresenter_http.json --action next_slide

# Test with mock action parameters
python3 scripts/test_module.py modules/propresenter_http.json --action trigger_slide --params '{"slide_index":5}'

# Test incoming hardware telemetry packet handling
python3 scripts/test_module.py modules/propresenter_http.json --packet '{"presentation":{"name":"Main Service"},"slide_index":3}'
```

---

## Complete Development Workflow

### Step 1: Initialize the Module
Create a new file in `modules/<device_id>.json` using one of the templates in `templates/`:
- `template_rest_bearer_polling.json` for REST APIs with Bearer/Token auth.
- `template_tcp_linedelimited.json` for line-delimited ASCII TCP protocols.
- `template_udp_binary.json` for binary packed UDP protocols.
- `template_websocket_jsonrpc.json` for WebSocket JSON-RPC 2.0 protocols.

### Step 2: Implement CommonJS Driver Hooks
Inside the `driverScript` string of the JSON module, implement the lifecycle functions:
```javascript
module.exports = {
    onConnect: function(transport, config) {
        engine.setStatus('connecting', 'Connecting to hardware...');
    },
    onTransportReady: function(transport, config) {
        engine.setStatus('connected', 'Ready');
    },
    onAction: function(transport, actionId, params) {
        if (actionId === 'power_on') {
            transport.send('PWR ON\r');
            return 'Dispatched power command';
        }
    },
    onMessage: function(transport, text, bytes) {
        if (text.indexOf('PWR=1') !== -1) {
            engine.setVariable('power_state', 'ON');
        }
    }
};
```

### Step 3: Run Headless Verification
```bash
python3 scripts/test_module.py modules/<device_id>.json
```

### Step 4: Hot-Deploy and Test Over Wi-Fi
```bash
python3 scripts/control_it_mcp.py deploy modules/<device_id>.json
python3 scripts/control_it_mcp.py test-action <device_id> <action_id>
```

### Step 5: Validate Repository Integrity
Ensure the schema is valid and SHA-256 integrity hashes are computed:
```bash
python3 scripts/validate.py
```

### Step 6: Submit a Pull Request
1. Commit your changes: `git checkout -b module/<device_id>`
2. Stage your files: `git add modules/<device_id>.json manifest.json`
3. Commit and open a PR against the `main` branch of `control-it-modules`.

---

## Driver Runtime Environment Reference

The embedded engine provides the following standard execution environment:

| Object / Method | Description |
| :--- | :--- |
| `module.exports = { ... }` | Exports lifecycle hooks (`onConnect`, `onTransportReady`, `onAction`, `onMessage`, `onDisconnect`). |
| `transport.send(data)` | Sends ASCII string or binary Buffer across the active transport. |
| `transport.sendBytes(byteArr)` | Transmits raw array of byte integers (0-255). |
| `transport.sendHex(hexStr)` | Transmits hex string (e.g., `'81 01 04 00 02 FF'`). |
| `transport.sendJson(obj)` | Serializes object to JSON and sends over WebSocket or TCP. |
| `engine.setVariable(id, val)` | Updates dynamic button title and color variable state in the app. |
| `engine.getVariable(id)` | Retrieves the current value of a module variable. |
| `engine.setStatus(state, msg)` | Sets connection state (`'connected'`, `'connecting'`, `'error'`, `'disconnected'`). |
| `engine.crypto.sha256(data)` | Computes SHA-256 hash as a hex string. |
| `engine.crypto.md5(data)` | Computes MD5 hash as a hex string. |
| `engine.crypto.hmacSha256(k, d)` | Computes HMAC-SHA256 hex digest. |
| `engine.binary.pack(fmt, values)`| Python-style binary struct pack (e.g., `'>HBB'`). |
| `engine.binary.unpack(fmt, data)`| Python-style binary struct unpack. |
| `engine.osc.encodeMessage(p, a)` | Encodes OSC address and argument array into binary packet. |
| `engine.osc.decodeMessage(bytes)`| Parses OSC binary packet into address string and argument list. |
| `Buffer.from(...)` | Complete Node.js-compatible Buffer polyfill for binary manipulation. |

---

## License

This repository and all community modules are licensed under the MIT License. See [LICENSE](./LICENSE) for details.
