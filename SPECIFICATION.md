# Control-It Companion Module Specification (v2.2)

This document provides the formal JSON schema specification, field types, and behavioral semantics for Control-It community and hardware integration modules.

---

## 1. Top-Level Module Schema

Every Control-It module is defined as a single JSON object matching [`schemas/module.schema.json`](file:///Users/micahcrandell/Documents/CODING/PROJECTS/iOSapps/Control-It/Control%20It/CommunityModules/schemas/module.schema.json).

```json
{
  "$schema": "https://raw.githubusercontent.com/micah1crandell/control-it-modules/main/schemas/module.schema.json",
  "id": "sony_visca_ptz",
  "name": "Sony VISCA over IP PTZ",
  "shortName": "VISCA PTZ",
  "manufacturer": "Sony",
  "version": "1.0.0",
  "author": "Control-It Team",
  "subtitle": "PTZ control via UDP port 52381",
  "descriptionText": "Controls Sony, PTZOptics, and BirdDog robotic cameras over local IP networks.",
  "iconName": "video.fill",
  "iconColorHex": "#007AFF",
  "defaultPort": "52381",
  "defaultProtocol": "UDP_SESSION",
  "defaultHost": "192.168.1.100",
  "helpUrl": "https://github.com/micah1crandell/control-it-modules",
  "connectionConfig": { ... },
  "variables": [ ... ],
  "actions": [ ... ],
  "driverScript": "..."
}
```

### Top-Level Fields

| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `$schema` | String | No | URL of the JSON Schema. Recommended for IDE autocomplete. |
| `id` | String | **Yes** | Lowercase alphanumeric identifier matching `^[a-z0-9_\-]+$`. Must be globally unique across all modules. |
| `name` | String | **Yes** | Human-readable title displayed in the module catalog. |
| `manufacturer`| String | **Yes** | Brand or creator (e.g. `Blackmagic Design`, `Sony`, `OBS Project`). Used for brand filtering. |
| `version` | String | **Yes** | Semantic version string `X.Y.Z` (e.g. `1.0.0`, `2.1.0`). Higher versions override lower versions on sync. |
| `actions` | Array | **Yes** | Array of `PremadeModuleAction` objects defining user commands. |
| `shortName` | String | No | 3-10 character badge/pill string for compact UI buttons and grid tags. |
| `author` | String | No | Author or maintainer name/handle. |
| `subtitle` | String | No | One-line summary of device capabilities. |
| `descriptionText`| String | No | Comprehensive notes on supported firmware, setup instructions, and pinouts. |
| `iconName` | String | No | Apple SF Symbols identifier (e.g. `video.fill`, `slider.vertical.3`, `tv.fill`). |
| `iconColorHex` | String | No | 6-character hex color code (e.g. `#FF9500`) used for UI card accenting. |
| `defaultPort` | String | No | Default TCP/UDP port number (e.g. `4455`, `9910`, `52381`). |
| `defaultProtocol`| String | No | Primary protocol enum: `TCP`, `UDP`, `WEBSOCKET`, `HTTP`, `HTTPS`, `OSC`, `MIDI`, `CUSTOM`. |
| `defaultHost` | String | No | Default placeholder IP address or hostname. |
| `origin` | String | No | `Built-In`, `Community`, or `Custom`. Handled automatically by the app. |
| `helpUrl` | String | No | Web link to device protocol documentation or GitHub repository. |
| `connectionConfig`| Object | No | Network transport, framing, and timeout settings. |
| `variables` | Array | No | List of dynamic variables published by this module. |
| `driverScript` | String | No | CommonJS JavaScript driver executed in JavaScriptCore. |

---

## 2. Connection Configuration (`connectionConfig`)

The `connectionConfig` block configures the low-level socket transport:

```json
{
  "connectionConfig": {
    "transport": "UDP_SESSION",
    "framing": "visca",
    "defaultPort": "52381",
    "defaultHost": "192.168.1.100",
    "autoConnectOnLaunch": true,
    "heartbeatIntervalMs": 10000,
    "handshakeTimeoutSeconds": 15.0,
    "retryIntervalSeconds": 3.0,
    "maxRetryAttempts": 10,
    "inactivityTimeoutSeconds": 20.0,
    "tls": false,
    "allowInsecureTLS": false,
    "urlPath": "/api/ws",
    "discovery": {
      "type": "bonjour",
      "serviceType": "_sony-camera._udp.",
      "autoFillHost": true
    },
    "setupFields": [ ... ]
  }
}
```

### Supported Transports (`transport`)

| Transport | Socket Engine | Description |
| :--- | :--- | :--- |
| `TCP` / `TCP_STREAM` | `TCPSessionTransport` | Persistent bidirectional TCP stream. Buffering is managed by `framing`. |
| `UDP` / `UDP_SESSION`| `UDPSessionTransport` | Native low-latency UDP datagram session with optional auxiliary listening port. |
| `WEBSOCKET` / `WS` | `NativeWebSocketTransport` | Full-duplex WebSocket client (`ws://`). Automatically handles ping/pong and frames. |
| `WSS` | `NativeWebSocketTransport` | Secure WebSocket client (`wss://`) over TLS. |
| `OBS_WEBSOCKET` | Native OBS Transport | Optimized WebSocket transport with built-in OBS v5 protocol acceleration. |
| `OSC` | UDP / OSC Session | Open Sound Control over UDP with native OSC packet encoding/decoding. |
| `HTTP` / `HTTPS` | URLSession Engine | Polled or ad-hoc REST/HTTP transport. |
| `CUSTOM` | Dynamic Transport | Custom script-driven transport. Defaults to TCP/UDP depending on defaultPort. |

### Stream Framing Modes (`framing`)

When using streaming transports (such as `TCP`), the native socket engine automatically splits incoming byte streams into individual messages before passing them to `onMessage(transport, text, bytes)`:

- **`"raw"`**: Default. Every chunk received from the OS socket is passed directly to `onMessage`.
- **`"line"`**: Splits on newline characters (`\n`).
- **`"crlf"`**: Splits on carriage return + line feed (`\r\n`). Strips delimiter from `text`.
- **`"visca"`**: Splits on the VISCA delimiter byte `0xFF`. Perfect for Sony/PTZ cameras.
- **`"slip"`**: Decodes RFC 1055 SLIP framing (delimiter `0xC0`).
- **`"length_2be"`**: Reads a 2-byte big-endian integer at the start of each packet indicating payload length.
- **`"length_4be"`**: Reads a 4-byte big-endian integer length header.
- **`"fixed_size_<N>"`**: Emits packets in fixed chunks of `<N>` bytes (e.g. `fixed_size_16`).

### Setup Wizard Fields (`setupFields`)
User-configurable connection inputs displayed in the app's Connection Setup Wizard:

```json
"setupFields": [
  {
    "id": "password",
    "label": "Device Password",
    "type": "Text",
    "placeholder": "Enter admin password",
    "isRequired": false,
    "isSecret": true
  },
  {
    "id": "camera_id",
    "label": "Camera VISCA Address",
    "type": "Dropdown",
    "defaultValue": "1",
    "dropdownChoices": ["1", "2", "3", "4", "5", "6", "7"]
  }
]
```
> [!NOTE]
> Fields marked `"isSecret": true` are stored securely in the iOS Keychain and accessed inside the driver via `engine.secret("password")`.

---

## 3. Dynamic Variables (`variables`)

Modules publish dynamic variables so that buttons, labels, and tally indicators can display live device telemetry:

```json
"variables": [
  {
    "id": "power_state",
    "name": "Power State",
    "descriptionText": "Current power mode (on, standby, warming)",
    "sampleValue": "on",
    "variableType": "String"
  },
  {
    "id": "zoom_position",
    "name": "Zoom Position",
    "descriptionText": "Current optical zoom value (0 to 16384)",
    "sampleValue": "4096",
    "variableType": "Number"
  }
]
```

### Variable Types
- `String`: Text values (e.g. `"Scene 1"`, `"Connected"`).
- `Number`: Numeric values (e.g. `42`, `-12.5`).
- `Boolean`: `"true"` or `"false"`.
- `JSON`: Serialized JSON strings for nested objects or arrays.

In UI templates and button labels, variables are referenced using double curly braces: `{{power_state}}` or `{{sony_visca_ptz:power_state}}`.

---

## 4. Actions Catalog (`actions`)

The `actions` array defines all user-triggerable commands.

```json
{
  "id": "pan_tilt_drive",
  "title": "Pan / Tilt Drive",
  "subtitle": "Continuous motion control",
  "descriptionText": "Moves camera in specified direction with adjustable speed.",
  "iconName": "arrow.up.and.down.and.arrow.left.and.right",
  "iconColorHex": "#007AFF",
  "inputs": [
    {
      "id": "direction",
      "label": "Direction",
      "type": "Dropdown",
      "defaultValue": "up",
      "dropdownChoices": ["up", "down", "left", "right", "upleft", "upright", "downleft", "downright", "stop"]
    },
    {
      "id": "speed",
      "label": "Pan Speed",
      "type": "Number",
      "defaultValue": "8",
      "minValue": 1,
      "maxValue": 24,
      "stepValue": 1
    }
  ],
  "dynamicTitleParsingRule": "CAM {{camera_id}}: {{direction}}",
  "dynamicColorRules": [
    {
      "condition": "{{camera_moving}} == 'true'",
      "colorName": "Red",
      "iconName": "record.circle.fill",
      "tallyStyle": "pulse",
      "label": "In Motion"
    }
  ]
}
```

### Action Input Fields (`inputs`)
- `id`: Variable key passed into `params` in `onAction(transport, actionId, params)`.
- `label`: Human-readable label in the action editor.
- `type`: `Text`, `Number`, `Dropdown`, or `Toggle`.
- `defaultValue`: Starting value when user adds the action.
- `dropdownChoices`: Array of selectable string options for `Dropdown`.
- `dynamicSource`: Dynamic options populated from variables (e.g. `"variables:obs_scenes"`).
- `minValue`, `maxValue`, `stepValue`: Numeric boundaries and stepper resolution.
- `isSecret`: Masks input in the UI.

### Live Feedback & Tally Rules (`dynamicColorRules`)
Allows buttons created from this action to automatically react to hardware state:
- `condition`: JavaScript-style boolean expression evaluating variables (e.g. `{{atem_program}} == 1`).
- `colorName`: Standard color (`Red`, `Green`, `Blue`, `Orange`, `Purple`, `Yellow`, `Gray`).
- `customColorHex`: Custom 6-digit hex color override.
- `iconName`: SF Symbol displayed when condition is active.
- `tallyStyle`: `'solid'` for steady border/background, or `'pulse'` for flashing tally alert.
- `label`: Status description shown in the button editor.

---

## 5. Driver Script (`driverScript`)

The driver script is an embedded CommonJS module executed in an isolated JavaScriptCore environment:

```javascript
module.exports = {
    onConnect: function(transport, config) {
        engine.setStatus("connecting", "Opening socket...");
    },
    onTransportReady: function(transport, config) {
        engine.setStatus("connected", "Ready");
    },
    onAction: function(transport, actionId, params) {
        if (actionId === "power_on") {
            transport.send("%1POWR 1\r");
            return "Power on sent";
        }
        return "Unknown action";
    },
    onMessage: function(transport, text, bytes) {
        if (text.includes("POWR=1")) {
            engine.setVariable("power_state", "on");
        }
    },
    onHeartbeat: function(transport) {
        transport.send("%1POWR ?\r");
    },
    onDisconnect: function() {
        engine.setStatus("disconnected", "Socket closed");
    }
};
```

For complete documentation of the runtime, global APIs, and polyfills, refer to [`DRIVER_RUNTIME_REFERENCE.md`](file:///Users/micahcrandell/Documents/CODING/PROJECTS/iOSapps/Control-It/Control%20It/CommunityModules/agent-pack/DRIVER_RUNTIME_REFERENCE.md).
