# Migrating Bitfocus Companion Modules to Control-It

This guide is designed for AV systems engineers and developers migrating existing **Bitfocus Companion modules** (`companion-module-base`) into native **Control-It modules**.

---

## 1. Architectural Differences

| Dimension | Bitfocus Companion Module | Control-It Module |
| :--- | :--- | :--- |
| **Runtime Environment** | Node.js (v18+) on desktop PC or server | JavaScriptCore (`ModuleRuntimeEnvironment`) directly on iOS/iPadOS |
| **Package Format** | Multi-file TypeScript / npm package with `yarn build` | Portable, single-file JSON with embedded JavaScript driver |
| **Network Sockets** | Node `net.Socket`, `dgram`, `ws` wrappers (`TCPHelper`, etc.) | Native Apple `Network.framework` sockets via unified `transport` |
| **UI Execution** | Web browser button matrix or Elgato Stream Deck | Native SwiftUI touch grid, interactive widgets, Siri Shortcuts |
| **State & Variables** | `self.setVariableValues({ key: val })` | `engine.setVariable(key, val)` / `engine.setVariables(dict)` |
| **Feedbacks / Tally** | Imperative boolean/advanced feedback callbacks | Declarative `dynamicColorRules` with reactive variable expressions |
| **Secrets Management** | Plaintext config or environment variables | Native encrypted iOS Keychain access via `engine.secret(key)` |

---

## 2. API Translation Mapping Table

### Lifecycle Hooks
| Bitfocus Companion (`companion-module-base`) | Control-It (`module.exports`) |
| :--- | :--- |
| `async init(config)` | `onConnect(transport, config)` & `onTransportReady(transport, config)` |
| `async configUpdated(config)` | `onConnect(transport, config)` |
| `async destroy()` | `onStop()` / `onDisconnect()` |
| `action(action)` | `onAction(transport, actionId, params)` |
| Periodic polling via `setInterval` | `onHeartbeat(transport)` via `heartbeatIntervalMs` |
| Socket data listener (`socket.on('data', ...)`) | `onMessage(transport, text, bytes)` |

### Socket & Transport
| Bitfocus Companion | Control-It |
| :--- | :--- |
| `this.tcp.send(Buffer.from(str))` | `transport.send(str)` |
| `this.tcp.send(Buffer.from([0x01, 0x02]))` | `transport.sendBytes([0x01, 0x02])` or `transport.sendHex("01 02")` |
| `this.ws.send(JSON.stringify(obj))` | `transport.sendJSON(obj)` |
| `this.udp.send(buffer, port, host)` | `transport.sendBytes(buffer)` |
| Manual request-response timeout tracking | `transport.sendAndAwait(payload, matcher, timeoutMs)` |

### Variables & Feedback
| Bitfocus Companion | Control-It |
| :--- | :--- |
| `this.setVariableDefinitions([...])` | `variables: [{ id: "...", name: "..." }]` in module JSON |
| `this.setVariableValues({ var_id: "val" })` | `engine.setVariable("var_id", "val")` |
| `this.checkFeedbacks('feedback_id')` | Automatic! UI recalculates `dynamicColorRules` when variables change. |
| `this.updateStatus(InstanceStatus.Ok)` | `engine.setStatus("connected", "Ready")` |
| `this.updateStatus(InstanceStatus.Connecting)` | `engine.setStatus("connecting", "Initializing...")` |

---

## 3. Side-by-Side Code Migration Example

### Before: Bitfocus Companion (TypeScript / Node.js)
```typescript
import { InstanceBase, runEntrypoint, InstanceStatus, TCPHelper } from '@companion-module/base'

class ProjectorInstance extends InstanceBase<Config> {
    private socket: TCPHelper | undefined

    async init(config: Config): Promise<void> {
        this.updateStatus(InstanceStatus.Connecting)
        this.socket = new TCPHelper(config.host, config.port)
        this.socket.on('connect', () => {
            this.updateStatus(InstanceStatus.Ok)
        })
        this.socket.on('data', (data) => {
            const text = data.toString()
            if (text.includes('%1POWR=1')) {
                this.setVariableValues({ power: 'on' })
                this.checkFeedbacks('power_state')
            }
        })
        this.setActionDefinitions({
            power_on: {
                name: 'Power On',
                options: [],
                callback: async () => {
                    this.socket?.send('%1POWR 1\r')
                }
            }
        })
    }
}
```

### After: Control-It Module (JSON + CommonJS)
```json
{
  "id": "pjlink_projector",
  "name": "PJLink Projector",
  "manufacturer": "Generic",
  "version": "1.0.0",
  "defaultPort": "4352",
  "defaultProtocol": "TCP",
  "connectionConfig": {
    "transport": "TCP",
    "framing": "crlf"
  },
  "variables": [
    { "id": "power", "name": "Power State", "sampleValue": "on" }
  ],
  "actions": [
    {
      "id": "power_on",
      "title": "Power On",
      "dynamicColorRules": [
        {
          "condition": "{{power}} == 'on'",
          "colorName": "Green",
          "label": "Projector Active"
        }
      ]
    }
  ],
  "driverScript": "module.exports = {\n  onConnect: function(transport, config) {\n    engine.setStatus('connecting', 'Connecting...');\n  },\n  onTransportReady: function(transport, config) {\n    engine.setStatus('connected', 'Ready');\n  },\n  onAction: function(transport, actionId, params) {\n    if (actionId === 'power_on') {\n      transport.send('%1POWR 1\\r');\n      return 'Power On sent';\n    }\n  },\n  onMessage: function(transport, text, bytes) {\n    if (text.includes('%1POWR=1')) {\n      engine.setVariable('power', 'on');\n    }\n  }\n};"
}
```

---

## 4. Key Advantages of the Control-It Pattern

1. **Zero Node.js Overhead**: Runs directly on mobile devices with instant startup and ultra-low battery consumption.
2. **Built-in Binary Primitives**: Native `engine.binary.pack` and `engine.checksum` make binary protocols significantly cleaner than raw Buffer slicing.
3. **Reactive Tally**: No need to manually trigger `checkFeedbacks()`. Button tally borders and colors automatically react to any `engine.setVariable()` mutation.
4. **Instant Over-the-Air Hot Reloading**: Update the module over Wi-Fi without restarting the app or compiling TypeScript packages.
