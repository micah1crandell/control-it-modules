# Control-It Driver Runtime API Reference

This document provides the complete API reference for writing JavaScript drivers for Control-It's `ModuleRuntimeEnvironment` (JSCore).

---

## 1. Runtime Environment & CommonJS Model

Every driver script executes inside an isolated Apple `JSContext` instance. The runtime provides a CommonJS-style export pattern:

```javascript
module.exports = {
    onConnect: function(transport, config) { ... },
    onTransportReady: function(transport, config) { ... },
    onAction: function(transport, actionId, params) { ... },
    onMessage: function(transport, text, bytes) { ... },
    onHeartbeat: function(transport) { ... },
    onDisconnect: function() { ... },
    onError: function(err) { ... },
    onStop: function() { ... }
};
```

### Global Availability
The following objects and utilities are available globally:
- `module`, `exports`
- `engine`: The native Swift bridge providing high-performance cryptography, buffers, checksums, binary packing, and UI state management.
- `Buffer`: Node.js-compatible Buffer polyfill (`Buffer.from()`, `Buffer.alloc()`, `buf.toString("hex")`, etc.).
- `console.log()`, `console.warn()`, `console.error()`.
- Standard ES6 primitives: `Promise`, `setTimeout()`, `clearTimeout()`, `setInterval()`, `clearInterval()`, `JSON`, `Math`, `Date`.

---

## 2. Lifecycle Hooks

### `exports.onConnect(transport, config)`
Called immediately when the device connection session is initialized, before the network socket has opened.
- **Parameters**:
  - `transport`: The transport controller object.
  - `config`: Dictionary of configured parameters (e.g. `config.host`, `config.port`, and custom `setupFields`).
- **Use Case**: Set initial UI status (`engine.setStatus("connecting", "Opening socket...")`).

### `exports.onTransportReady(transport, config)`
Called as soon as the underlying TCP/UDP/WS socket successfully connects.
- **Parameters**:
  - `transport`: The transport controller object.
  - `config`: Configuration dictionary.
- **Use Case**: Send protocol handshake, authenticate with credentials, or query initial device state.

### `exports.onAction(transport, actionId, params)`
Called when an action is triggered by a button press, automation rule, or external trigger.
- **Parameters**:
  - `actionId`: String matching the action's `id`.
  - `params`: Key-value dictionary of action inputs configured by the user.
- **Return Value**:
  - Return a **String** for synchronous actions (e.g. `return "Switched to Scene 1"`).
  - Return a **`Promise<String>`** for asynchronous actions that require awaiting a hardware acknowledgement.

### `exports.onMessage(transport, text, bytes)`
Called whenever data arrives from the device.
- **Parameters**:
  - `transport`: The transport controller object.
  - `text`: Decoded UTF-8 string (or empty if non-text binary). If stream framing is enabled (`line`, `crlf`, etc.), `text` contains the framed payload.
  - `bytes`: Standard JavaScript Array of integers (0-255) representing raw packet bytes.

### `exports.onHeartbeat(transport)`
Called periodically if `heartbeatIntervalMs` or `heartbeatIntervalSeconds` is configured in `connectionConfig`.
- **Use Case**: Send keepalive pings (e.g. `transport.send("PING\r\n")`) to prevent timeouts.

### `exports.onDisconnect()`
Called when the underlying socket is closed or dropped.
- **Use Case**: Update status to disconnected or clean up internal timers.

### `exports.onError(errorMessage)`
Called when a transport or network-level error occurs.

### `exports.onStop()`
Called when the user disables, reconfigures, or deletes the connection. Tear down any long-running state.

---

## 3. Transport API (`transport.*`)

The `transport` object is passed into lifecycle hooks to send data to the connected device:

### `transport.send(text)`
Sends a UTF-8 string to the device.
```javascript
transport.send("%1POWR 1\r");
```

### `transport.sendBytes(bytesOrBuffer)`
Sends raw bytes. Accepts either a JavaScript Array of byte integers (`[0x81, 0x01, 0x04, 0x00, 0x02, 0xFF]`) or a `Buffer` object.
```javascript
transport.sendBytes([0x81, 0x01, 0x04, 0x00, 0x02, 0xFF]);
```

### `transport.sendHex(hexString)`
Convenience method to send bytes from a spaced or unspaced hex string.
```javascript
transport.sendHex("81 01 04 00 02 FF");
```

### `transport.sendJSON(object)`
Serializes a JavaScript object to JSON and sends it.
```javascript
transport.sendJSON({
    "request-type": "SetCurrentProgramScene",
    "scene-name": params.scene
});
```

### `transport.sendAndAwait(payload, matcherFnOrString, timeoutMs)`
Sends a payload and returns a `Promise` that resolves when a matching incoming response arrives from the device, or rejects on timeout.
- **Parameters**:
  - `payload`: String, Buffer, or byte array to send.
  - `matcherFnOrString`: Either a String (checks if response contains it) or a predicate function `function(text, bytes): boolean`.
  - `timeoutMs`: Timeout in milliseconds (default: 5000).
- **Example**:
```javascript
return transport.sendAndAwait("%1POWR 1\r", "%1POWR=OK", 3000)
    .then(function(response) {
        engine.setVariable("power", "on");
        return "Power turned on successfully";
    });
```

---

## 4. Engine Utilities (`engine.*`)

The global `engine` object is a native Swift bridge providing reactive state management and high-performance AV algorithms.

### 4.1 State & UI Management
- **`engine.setVariable(key, value)`**: Sets a live dynamic variable. The UI updates instantly. Value is cast to String.
  ```javascript
  engine.setVariable("program_input", "CAM 1");
  ```
- **`engine.getVariable(key)`**: Retrieves the current value of a variable.
- **`engine.setVariables(dictionary)`**: Batches multiple variable updates in a single UI render pass.
  ```javascript
  engine.setVariables({
      "power": "on",
      "volume": "-12.5",
      "mute": "false"
  });
  ```
- **`engine.setStatus(status, message)`**: Sets the connection status badge in the Control-It UI.
  - Standard status strings: `"connected"`, `"connecting"`, `"authenticating"`, `"failed"`, `"disconnected"`, `"error"`.
  ```javascript
  engine.setStatus("connected", "Ready - Firm: v3.4.1");
  ```
- **`engine.reconnect()`**: Forces the transport to close and immediately attempt a clean reconnection.
- **`engine.fail(reason)`**: Marks the connection as failed with an error message and stops reconnect loops.
- **`engine.secret(key)`**: Safely retrieves a sensitive credential (e.g. password or API key) stored in the iOS Keychain from `setupFields`.
  ```javascript
  var token = engine.secret("api_token");
  ```
- **`engine.log(message)`**: Emits a timestamped log to the driver console.

---

### 4.2 Native Buffer Suite (`engine.buffer.*`)
High-performance native binary manipulation:
- `engine.buffer.create(size)`: Returns zeroed byte array of length `size`.
- `engine.buffer.fromHex(hexString)`: Converts hex string to byte array.
- `engine.buffer.toHex(bytes)`: Formats byte array as uppercase hex string.
- `engine.buffer.slice(bytes, start, end)`: Slices byte array.
- `engine.buffer.concat(buf1, buf2)`: Merges two byte arrays.

#### Number Reading & Writing (Big & Little Endian)
| Method | Description |
| :--- | :--- |
| `readUInt8(buf, offset)` / `writeInt8(buf, offset, val)` | 8-bit unsigned / signed integer |
| `readUInt16BE(buf, offset)` / `readUInt16LE(buf, offset)` | 16-bit unsigned integer (BE / LE) |
| `writeUInt16BE(buf, offset, val)` / `writeUInt16LE(...)` | Write 16-bit unsigned integer |
| `readInt16BE(buf, offset)` / `readInt16LE(buf, offset)` | 16-bit signed integer |
| `readUInt32BE(buf, offset)` / `readUInt32LE(buf, offset)` | 32-bit unsigned integer |
| `writeUInt32BE(buf, offset, val)` / `writeUInt32LE(...)` | Write 32-bit unsigned integer |
| `readFloatBE(buf, offset)` / `writeFloatBE(buf, offset, val)` | 32-bit IEEE 754 Floating Point |
| `readDoubleBE(buf, offset)` / `writeDoubleLE(...)` | 64-bit IEEE 754 Double Precision |
| `readBigUInt64BE(buf, offset)` | 64-bit unsigned integer (as String) |
| `readString(buf, offset, len)` | Reads ASCII/UTF-8 string slice |
| `writeString(buf, offset, str)` | Writes string bytes into buffer |

---

### 4.3 Binary Struct Packing (`engine.binary.*`)
Python-style `struct.pack` and `struct.unpack` for binary hardware protocols:

```javascript
// Pack a 12-byte ATEM command: 2-byte length, 2 skipped, 4-char cmd, 2-byte input, 2 skipped
var packet = engine.binary.pack(">Hxx4sHxx", [12, "DCut", 0]);
transport.sendBytes(packet);

// Unpack incoming bytes
var fields = engine.binary.unpack(">Hxx4sH", bytes);
var length = fields[0];
var command = fields[1];
var input = fields[2];
```

#### Format Specifiers:
- `>`: Big-Endian, `<`: Little-Endian
- `B`: uint8, `b`: int8
- `H`: uint16, `h`: int16
- `I`: uint32, `i`: int32
- `Q`: uint64, `q`: int64
- `f`: float (32-bit), `d`: double (64-bit)
- `s`: string (e.g. `4s` = 4-byte ASCII string)
- `x`: pad byte (skip 1 byte)

---

### 4.4 Cryptography Suite (`engine.crypto.*`)
- `engine.crypto.sha256(string)`: Returns hex SHA-256 hash.
- `engine.crypto.sha1(string)`: Returns hex SHA-1 hash.
- `engine.crypto.md5(string)`: Returns hex MD5 hash (used in PJLink auth).
- `engine.crypto.hmacSHA256(key, message)`: Computes HMAC-SHA256 signature.
- `engine.crypto.base64Encode(string)`: Base64 encodes string.
- `engine.crypto.base64Decode(string)`: Decodes base64 string.

---

### 4.5 Checksums (`engine.checksum.*`)
Standard broadcast and industrial CRC algorithms:
- `engine.checksum.crc16Modbus(bytes)`: Returns 16-bit integer Modbus CRC.
- `engine.checksum.crc16CCITT(bytes)`: CCITT standard CRC.
- `engine.checksum.crc32(bytes)`: Standard IEEE 802.3 32-bit CRC.
- `engine.checksum.xor(bytes)`: Longitudinal Redundancy Check (XOR sum).
- `engine.checksum.sum8(bytes)`: 8-bit additive checksum.
- `engine.checksum.twosComplement(bytes)`: Two's complement additive checksum.

---

### 4.6 Open Sound Control (`engine.osc.*`)
Native OSC 1.0 encoding and decoding:
- **`engine.osc.encode(address, argsArray)`**:
  ```javascript
  // Returns raw byte array of OSC packet
  var packet = engine.osc.encode("/ch/01/mix/fader", [0.75]);
  transport.sendBytes(packet);
  ```
- **`engine.osc.decode(bytes)`**:
  ```javascript
  var oscMsg = engine.osc.decode(bytes);
  // oscMsg = { address: "/ch/01/mix/fader", args: [0.75] }
  ```

---

### 4.7 Local Driver Storage (`engine.storage.*`)
Isolated persistent key-value storage per module:
- `engine.storage.set(key, value)`
- `engine.storage.get(key)`
- `engine.storage.remove(key)`
- `engine.storage.clear()`
- `engine.storage.keys()`
