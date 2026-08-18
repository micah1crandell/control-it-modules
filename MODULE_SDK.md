# Control-It Community Module SDK

Welcome to the Control-It Community Module SDK. Community modules allow you to write JavaScript driver scripts that connect to persistent network devices via TCP, UDP, or WebSocket, sending commands and receiving real-time telemetry.

## 1. Overview

Community modules in Control-It act as a bridge between the app's UI and the network layer. When a module is loaded, the app instantiates a JavaScript runtime environment (`ModuleRuntimeEnvironment`) isolated for that device. 

Your driver script implements a CommonJS-style `module.exports` object containing lifecycle hooks (`onConnect`, `onAction`, `onMessage`, etc.). The app handles the low-level socket connections (`PersistentTransport`) and provides a rich `engine` API and standard polyfills (Node.js `Buffer`, `Promise`, `setTimeout`, etc.) for you to use.

## 2. Quick Start

Here's a minimal TCP module that connects, sends a command on action, and logs responses:

```javascript
module.exports = {
    onConnect: function(transport, config) {
        engine.log("Connecting to " + config.host);
        engine.setStatus("connecting", "Initializing connection...");
    },
    
    onTransportReady: function(transport, config) {
        engine.log("Transport ready!");
        engine.setStatus("connected", "Ready");
        // Send a handshake or initial command
        transport.send("INIT\\r\\n");
    },
    
    onAction: function(transport, actionId, params) {
        if (actionId === "power_on") {
            transport.send("POWER ON\\r\\n");
            return "Sent Power On";
        }
        return "Unknown action";
    },
    
    onMessage: function(transport, text, bytes) {
        engine.log("Received: " + text);
        if (text.includes("POWER=ON")) {
            engine.setVariable("device_power", "true");
        }
    }
};
```

## 3. Module Lifecycle

The typical lifecycle of a persistent connection is:

1. **Install/Configure:** User adds the module and enters IP/Port/Credentials.
2. **Connect (`onConnect`):** Called before the socket is actually opened. Good place to set initial status.
3. **Transport Ready (`onTransportReady`):** The socket is established (or WebSocket connected). Handshakes happen here.
4. **Message Loop (`onMessage`):** Called continuously whenever data arrives from the device.
5. **Actions (`onAction`):** Called when a user presses a button or an automation triggers an action.
6. **Heartbeat (`onHeartbeat`):** Called periodically based on the `heartbeatIntervalMs` configuration.
7. **Disconnect (`onDisconnect`):** The transport was closed (intentionally or dropped).
8. **Stop (`onStop`):** The user deleted or disabled the connection.

## 4. Lifecycle Hooks Reference

Your script should export these functions via `module.exports`:

### `exports.onConnect(transport, config)`
Called when the device manager initiates a connection, before the socket connects. 
- `transport`: The transport object.
- `config`: Dictionary of user-configured settings (e.g., `config.host`, `config.port`, custom fields).

### `exports.onTransportReady(transport, config)`
Called immediately after the underlying TCP/UDP/WS socket successfully connects. Use this to send login credentials or initial state queries.

### `exports.onMessage(transport, text, bytes)`
Called whenever data is received from the device.
- `text`: The payload as a string (if decodable).
- `bytes`: Array of integers (0-255) representing the raw bytes.

### `exports.onAction(transport, actionId, params)`
Called to execute a user-triggered action.
- `actionId`: String matching the action definition ID.
- `params`: Dictionary of user inputs (e.g., `params.channel`).
- **Returns:** A string (status message) or a `Promise` resolving to a string.

### `exports.onHeartbeat(transport)`
Called periodically if `heartbeatIntervalMs` is set in configuration metadata. Use to send keepalives (e.g., `transport.send("PING")`).

### `exports.onDisconnect()`
Called when the socket drops or is closed.

### `exports.onStop()`
Called when the connection is completely torn down and destroyed.

### `exports.onError(errorMessage)`
Called when an internal socket or transport error occurs.

## 5. Transport API Reference

The `transport` object is provided in hook signatures. It allows sending data.

- **`transport.send(string)`**  
  Sends a UTF-8 string payload. Returns `true` if queued.

- **`transport.sendBytes(arrayOrBuffer)`**  
  Sends raw bytes. Accepts a regular JS Array of numbers, or a `Buffer` object.

- **`transport.sendHex(hexString)`**  
  Sends bytes from a hex string (e.g., `"FF 01 04 00"`).

- **`transport.sendJSON(object)`**  
  Serializes the object to JSON and sends it.

- **`transport.sendAndAwait(payload, matcherFn, timeoutMs)`**  
  Sends a payload and waits for a specific response. Returns a `Promise`.
  - `payload`: String, Buffer, Array, or Object.
  - `matcherFn`: A function `(text, bytes)` that returns `true` if this is the expected response, or a String to check if `text` contains it.
  - `timeoutMs`: Number of milliseconds before the promise rejects (default 5000).

## 6. Engine APIs

The `engine` object is globally available and provides a rich set of utility suites.

### Variables & State
- **`engine.setVariable(key, value)`**: Sets a global live variable that UI elements can bind to. Value is stored as string.
- **`engine.getVariable(key)`**: Returns the current value of a variable.
- **`engine.setVariables(dict)`**: Sets multiple variables at once.
- **`engine.setStatus(status, message)`**: Updates the connection UI status. Standard statuses: `"connected"`, `"connecting"`, `"authenticating"`, `"failed"`, `"disconnected"`, `"error"`.

### Logging & Utilities
- **`console.log`, `console.warn`, `console.error`**: Polyfilled standard logging.
- **`engine.log(msg)`**: Sends a log to the driver log feed.
- **`engine.reconnect()`**: Forces the transport to drop and reconnect.
- **`engine.secret(key)`**: Retrieves a sensitive configuration value securely stored in the iOS Keychain.

### Buffer API (`engine.buffer.*`)
While the Node.js `Buffer` polyfill is available globally, the native `engine.buffer` suite is highly performant:
- `create(size)`, `fromHex(hexStr)`, `toHex(buffer)`
- `readUInt8(buf, offset)`, `writeInt8(buf, offset, val)`
- `readUInt16BE`, `readUInt16LE`, `writeUInt16BE`, etc.
- `readUInt32BE`, `readInt32LE`, etc.
- `readFloatBE`, `writeDoubleLE`, etc.
- `readBigUInt64BE`, `writeBigInt64LE` (Uses String/BigInt representation)
- `readString(buf, offset, len)`, `writeString(buf, offset, str)`
- `slice(buf, start, end)`, `concat(buf1, buf2)`

### Crypto API (`engine.crypto.*`)
- `sha256(string)`, `sha1(string)`, `md5(string)`
- `hmacSHA256(key, message)`
- `base64Encode(string)`, `base64Decode(string)`

### Binary Struct API (`engine.binary.*`)
Python-style packing and unpacking.
- `pack(format, values)`: e.g., `engine.binary.pack(">4sHHB", ["TEST", 1234, 5678, 42])`
- `unpack(format, buffer)`

### Checksums (`engine.checksum.*`)
- `crc16Modbus(bytes)`, `crc16CCITT(bytes)`, `crc16XMODEM(bytes)`
- `xor(bytes)`, `sum8(bytes)`, `twosComplement(bytes)`

### OSC Primitives (`engine.osc.*`)
- `encode(address, argsArray)`: Returns byte array of OSC message.
- `decode(buffer)`: Returns object `{ address: "/foo", args: [...] }`.

## 7. Connection Configuration

The module definition (JSON/Swift) provides a `ModuleConnectionConfig` containing defaults. Relevant fields that dictate transport behavior:

- `protocolType` / `transport`: "TCP", "TCP_STREAM", "UDP", "UDP_SESSION", "WEBSOCKET", "WS", "WSS", "OBS_WEBSOCKET"
- `framing`: How incoming streams are chunked into `onMessage` calls.
  - `"raw"` (default)
  - `"lineDelimiter"` (CR/LF delimiter)
  - `"byteDelimiter"` (e.g. 0xFF for VISCA)
  - `"lengthPrefix"` (2-byte big-endian length prefix, etc.)
  - `"slipFraming"` (RFC 1055 SLIP)
  - `"fixedSize"`
- `heartbeatIntervalSeconds` / `heartbeatIntervalMs`: Interval to call `onHeartbeat`
- `enableTLS`, `allowInsecureTLS`
- `urlPath`: For WebSockets (e.g., `/api`)
- `localPort`, `allowBroadcast`, `multicastGroup`: For UDP

## 8. Transport Types

Control-It supports several underlying transports. Specify them in your module's connection config:

- **"TCP" / "TCP_STREAM"**: Continuous byte stream. Use `framing` options to avoid handling partial packets manually.
- **"UDP" / "UDP_SESSION"**: Connectionless datagrams. `onMessage` corresponds to exactly one UDP packet.
- **"WEBSOCKET" / "WS" / "WSS" / "OBS_WEBSOCKET"**: WebSocket framing. Payload is inherently framed by WS text/binary frames.
- **"CUSTOM"**: Defaults to UDP if not mapped explicitly.

## 9. Example Modules

### Example 1: TCP Device (Projector using CRLF framing)
```javascript
module.exports = {
    onTransportReady: function(transport, config) {
        engine.setStatus("connected", "TCP Ready");
    },
    onAction: function(transport, actionId, params) {
        if (actionId === "shutter_open") {
            transport.send("%1AVMT 30\\r");
            return "Shutter Open Sent";
        }
    },
    onMessage: function(transport, text, bytes) {
        // Because framing is "line", `text` is guaranteed to be a complete line
        if (text.includes("POWR=1")) {
            engine.setVariable("power_state", "on");
        }
    }
};
```

### Example 2: WebSocket Device (JSON API)
```javascript
module.exports = {
    onTransportReady: function(transport, config) {
        transport.sendJSON({
            requestType: "Identify",
            client: "Control-It",
            token: engine.secret("password")
        });
    },
    onAction: function(transport, actionId, params) {
        if (actionId === "switch_scene") {
            transport.sendJSON({
                requestType: "SetCurrentProgramScene",
                sceneName: params.scene_name
            });
            return "Switching Scene...";
        }
    },
    onMessage: function(transport, text, bytes) {
        var msg;
        try { msg = JSON.parse(text); } catch(e) { return; }
        
        if (msg.op === 0) { // Identified
            engine.setStatus("connected", "Authenticated");
        }
    }
};
```

### Example 3: UDP Binary Device (ATEM style)
```javascript
module.exports = {
    onAction: function(transport, actionId, params) {
        if (actionId === "cut") {
            // Pack a 12-byte header + command
            var cmd = engine.binary.pack(">Hxx4sHxx", [12, "DCut", 0]);
            transport.sendBytes(cmd);
            return "Cut executed";
        }
    },
    onMessage: function(transport, text, bytes) {
        // Parse raw bytes array
        if (bytes.length >= 8) {
            var length = engine.buffer.readUInt16BE(bytes, 0);
            var commandStr = engine.buffer.readString(bytes, 4, 4);
            if (commandStr === "PrgI") {
                var inputId = engine.buffer.readUInt16BE(bytes, 8);
                engine.setVariable("program_input", String(inputId));
            }
        }
    }
};
```

## 10. Best Practices

1. **Async Actions:** If your action needs to wait for a response, return a `Promise`. `transport.sendAndAwait` is perfect for this.
2. **Variable Updates:** Call `engine.setVariable()` generously. It allows users to build dashboards with dynamic feedback text and colors based on your module's state.
3. **Heartbeats:** If the protocol requires keep-alives to prevent disconnects, define `heartbeatIntervalMs` and implement `onHeartbeat` rather than creating manual `setInterval` loops.
4. **Secrets:** Never hardcode passwords. Access user-configured secrets securely via `engine.secret("password_field")` where `password_field` is defined as a secure connection config input.

## 11. Debugging

1. **Logging:** Use `console.log()` or `engine.log()`. These output directly to the "Action Console" and driver log viewers inside the Control-It app.
2. **Errors:** Uncaught exceptions in your script will be logged as `[Module Driver JS Error]`. Catch `JSON.parse` errors explicitly in `onMessage`.
3. **State Updates:** Use `engine.setStatus("failed", "Wrong password")` if you detect authentication issues, so the user knows exactly why the connection isn't working.

---
_SDK Version 1.0 — Generated for Control-It ModuleRuntimeEnvironment_
