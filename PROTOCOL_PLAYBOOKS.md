# Control-It Protocol Playbooks & Implementation Recipes

This document provides complete, production-tested JavaScript driver patterns for the most common AV and broadcast automation protocols. Copy, adapt, and use these as reference architectures when generating new modules.

---

## Playbook 1: Line-Delimited TCP ASCII (PJLink Projector with MD5 Auth)

Used by: **Projectors (Epson, Panasonic, Sony, Christie), Extron matrix switchers, Kramer, RossTalk, Telnet gear**.

### Configuration
- **Transport**: `TCP`
- **Framing**: `"crlf"`
- **Default Port**: `4352`

### Driver Script
```javascript
module.exports = {
    authChallenge: null,
    
    onConnect: function(transport, config) {
        engine.setStatus("connecting", "Connecting to projector...");
    },
    
    onTransportReady: function(transport, config) {
        engine.setStatus("connecting", "Waiting for projector handshake...");
    },
    
    onMessage: function(transport, text, bytes) {
        text = text.trim();
        engine.log("Projector >> " + text);
        
        // 1. PJLink Handshake & Authentication Challenge
        if (text.startsWith("PJLINK 1 ")) {
            // Projector requires MD5 authentication
            var challenge = text.substring(9, 17);
            var password = engine.secret("password") || "";
            var digest = engine.crypto.md5(challenge + password);
            this.authChallenge = digest;
            
            engine.log("Authenticated with challenge MD5: " + digest);
            engine.setStatus("connected", "Authenticated");
            
            // Query initial power state and lamp hours
            transport.send(this.formatCommand("POWR", "?"));
            transport.send(this.formatCommand("LAMP", "?"));
            return;
        } else if (text.startsWith("PJLINK 0")) {
            // No authentication required
            this.authChallenge = "";
            engine.setStatus("connected", "Ready (No Auth)");
            transport.send(this.formatCommand("POWR", "?"));
            return;
        }
        
        // 2. Parse Command Responses
        // Format: %1POWR=1 (Power On), %1POWR=0 (Standby), %1POWR=2 (Cooling), %1POWR=3 (Warm-up)
        if (text.includes("%1POWR=")) {
            var val = text.split("=")[1];
            var state = "unknown";
            if (val === "0") state = "standby";
            else if (val === "1") state = "on";
            else if (val === "2") state = "cooling";
            else if (val === "3") state = "warmup";
            engine.setVariable("power_state", state);
        }
        
        if (text.includes("%1LAMP=")) {
            // Format: %1LAMP=2450 1 (hours, lamp on/off)
            var lampHours = text.split("=")[1].split(" ")[0];
            engine.setVariable("lamp_hours", lampHours);
        }
    },
    
    onAction: function(transport, actionId, params) {
        if (actionId === "power_on") {
            transport.send(this.formatCommand("POWR", "1"));
            return "Sent Power On";
        } else if (actionId === "power_off") {
            transport.send(this.formatCommand("POWR", "0"));
            return "Sent Power Off";
        } else if (actionId === "input_switch") {
            transport.send(this.formatCommand("INPT", params.source));
            return "Switched input to " + params.source;
        } else if (actionId === "shutter") {
            var state = params.state === "mute" ? "1" : "0";
            transport.send(this.formatCommand("AVMT", state + "1"));
            return "Set AV Mute to " + params.state;
        }
        return "Unknown action";
    },
    
    onHeartbeat: function(transport) {
        transport.send(this.formatCommand("POWR", "?"));
    },
    
    onDisconnect: function() {
        engine.setStatus("disconnected", "Projector connection closed");
    },
    
    formatCommand: function(cmd, param) {
        var prefix = this.authChallenge ? this.authChallenge : "";
        return prefix + "%1" + cmd + " " + param + "\r";
    }
};
```

---

## Playbook 2: Binary UDP with Byte Delimiter (Sony VISCA over IP)

Used by: **Sony, PTZOptics, BirdDog, Marshall, NewTek NDI/PTZ cameras**.

### Configuration
- **Transport**: `UDP_SESSION`
- **Framing**: `"visca"` (splits incoming packets on `0xFF`)
- **Default Port**: `52381`

### Driver Script
```javascript
module.exports = {
    sequenceNumber: 1,
    
    onConnect: function(transport, config) {
        engine.setStatus("connecting", "Starting VISCA UDP session...");
    },
    
    onTransportReady: function(transport, config) {
        engine.setStatus("connected", "Ready");
        this.sequenceNumber = 1;
        // Reset sequence number in camera
        transport.sendBytes([0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01]);
    },
    
    onMessage: function(transport, text, bytes) {
        // VISCA Over IP Header is 8 bytes:
        // [0..1] Payload type: 0x0111 (Reply), 0x0100 (Command)
        // [2..3] Payload length
        // [4..7] Sequence number
        if (bytes.length < 8) return;
        
        var payloadType = (bytes[0] << 8) | bytes[1];
        if (payloadType === 0x0111) { // VISCA Reply
            var viscaBytes = bytes.slice(8);
            if (viscaBytes.length >= 3) {
                var socketNum = (viscaBytes[1] >> 4) & 0x0F;
                var msgType = viscaBytes[1] & 0x0F;
                
                if (msgType === 0x04) { // ACK
                    engine.setVariable("camera_busy", "true");
                } else if (msgType === 0x05) { // Completion
                    engine.setVariable("camera_busy", "false");
                }
            }
        }
    },
    
    onAction: function(transport, actionId, params) {
        var viscaCmd = [];
        var camAddr = 0x81; // Camera 1
        
        if (actionId === "pan_tilt") {
            var panSpeed = parseInt(params.pan_speed, 10) || 8;
            var tiltSpeed = parseInt(params.tilt_speed, 10) || 8;
            var dir = params.direction;
            
            var pDir = 0x03, tDir = 0x03; // Stop
            if (dir === "up") { pDir = 0x03; tDir = 0x01; }
            else if (dir === "down") { pDir = 0x03; tDir = 0x02; }
            else if (dir === "left") { pDir = 0x01; tDir = 0x03; }
            else if (dir === "right") { pDir = 0x02; tDir = 0x03; }
            
            viscaCmd = [camAddr, 0x01, 0x06, 0x01, panSpeed, tiltSpeed, pDir, tDir, 0xFF];
        } else if (actionId === "zoom") {
            var zSpeed = parseInt(params.speed, 10) || 4;
            var zCode = 0x00; // Stop
            if (params.mode === "tele") zCode = 0x20 | (zSpeed & 0x07);
            else if (params.mode === "wide") zCode = 0x30 | (zSpeed & 0x07);
            
            viscaCmd = [camAddr, 0x01, 0x04, 0x07, zCode, 0xFF];
        } else if (actionId === "recall_preset") {
            var preset = parseInt(params.preset_num, 10) || 0;
            viscaCmd = [camAddr, 0x01, 0x04, 0x3F, 0x02, preset, 0xFF];
        }
        
        if (viscaCmd.length > 0) {
            this.sendVisca(transport, viscaCmd);
            return "Command sent";
        }
        return "Unknown action";
    },
    
    sendVisca: function(transport, viscaPayload) {
        // Wrap with 8-byte Sony VISCA-over-IP Header
        // 0x0100 = VISCA Command
        var header = [
            0x01, 0x00,
            (viscaPayload.length >> 8) & 0xFF, viscaPayload.length & 0xFF,
            (this.sequenceNumber >> 24) & 0xFF, (this.sequenceNumber >> 16) & 0xFF,
            (this.sequenceNumber >> 8) & 0xFF, this.sequenceNumber & 0xFF
        ];
        this.sequenceNumber = (this.sequenceNumber + 1) & 0xFFFFFFFF;
        var fullPacket = header.concat(viscaPayload);
        transport.sendBytes(fullPacket);
    }
};
```

---

## Playbook 3: WebSocket with JSON-RPC & Auth (OBS Studio v5)

Used by: **OBS Studio, vMix, HyperDeck, Node-RED, Web APIs**.

### Configuration
- **Transport**: `WEBSOCKET`
- **Framing**: `"raw"`
- **Default Port**: `4455`

### Driver Script
```javascript
module.exports = {
    onConnect: function(transport, config) {
        engine.setStatus("connecting", "Connecting to OBS WebSocket...");
    },
    
    onTransportReady: function(transport, config) {
        engine.setStatus("connecting", "Awaiting Hello packet...");
    },
    
    onMessage: function(transport, text, bytes) {
        var msg;
        try { msg = JSON.parse(text); } catch(e) { return; }
        
        var op = msg.op;
        var d = msg.d;
        
        // 1. Hello (op: 0) -> Identify (op: 1)
        if (op === 0) {
            var identifyPayload = {
                rpcVersion: 1,
                eventSubscriptions: 33 // General + Scenes + Outputs
            };
            
            if (d.authentication) {
                var password = engine.secret("password") || "";
                var salt = d.authentication.salt;
                var challenge = d.authentication.challenge;
                
                // OBS v5 auth formula: SHA256(SHA256(pass + salt) + challenge)
                var secretHash = engine.crypto.sha256(password + salt);
                var secretBase64 = engine.crypto.base64Encode(secretHash);
                var authHash = engine.crypto.sha256(secretBase64 + challenge);
                identifyPayload.authentication = engine.crypto.base64Encode(authHash);
            }
            
            transport.sendJSON({ op: 1, d: identifyPayload });
            return;
        }
        
        // 2. Identified (op: 2) -> Connected!
        if (op === 2) {
            engine.setStatus("connected", "Connected to OBS v" + d.obsWebSocketVersion);
            // Query current program scene
            this.sendRequest(transport, "GetCurrentProgramScene", {});
            this.sendRequest(transport, "GetRecordStatus", {});
            return;
        }
        
        // 3. RequestResponse (op: 7)
        if (op === 7) {
            if (d.requestType === "GetCurrentProgramScene" && d.responseData) {
                engine.setVariable("current_scene", d.responseData.currentProgramSceneName);
            } else if (d.requestType === "GetRecordStatus" && d.responseData) {
                engine.setVariable("recording", d.responseData.outputActive ? "true" : "false");
            }
            return;
        }
        
        // 4. Events (op: 5)
        if (op === 5) {
            if (d.eventType === "CurrentProgramSceneChanged") {
                engine.setVariable("current_scene", d.eventData.sceneName);
            } else if (d.eventType === "RecordStateChanged") {
                engine.setVariable("recording", d.eventData.outputActive ? "true" : "false");
            }
        }
    },
    
    onAction: function(transport, actionId, params) {
        if (actionId === "set_scene") {
            this.sendRequest(transport, "SetCurrentProgramScene", {
                sceneName: params.scene_name
            });
            return "Switched scene to " + params.scene_name;
        } else if (actionId === "toggle_record") {
            this.sendRequest(transport, "ToggleRecord", {});
            return "Toggled recording";
        }
        return "Unknown action";
    },
    
    sendRequest: function(transport, requestType, requestData) {
        var reqId = "req_" + Date.now();
        transport.sendJSON({
            op: 6,
            d: {
                requestType: requestType,
                requestId: reqId,
                requestData: requestData
            }
        });
    }
};
```

---

## Playbook 4: Open Sound Control (OSC) for Audio Consoles (Behringer / Midas X32)

Used by: **Behringer X32, X-Air, Midas M32, QLab, Cockos Reaper, Yamaha TF**.

### Configuration
- **Transport**: `OSC` (UDP)
- **Default Port**: `10023`
- **Heartbeat**: `9000ms` (X32 requires `/xremote` every 10s to keep meter telemetry alive)

### Driver Script
```javascript
module.exports = {
    onConnect: function(transport, config) {
        engine.setStatus("connecting", "Opening OSC port...");
    },
    
    onTransportReady: function(transport, config) {
        engine.setStatus("connected", "Ready");
        // Request console info
        var infoPacket = engine.osc.encode("/info", []);
        transport.sendBytes(infoPacket);
        // Subscribe to live telemetry
        this.onHeartbeat(transport);
    },
    
    onMessage: function(transport, text, bytes) {
        var osc = engine.osc.decode(bytes);
        if (!osc || !osc.address) return;
        
        var addr = osc.address;
        var args = osc.args || [];
        
        if (addr === "/info" && args.length >= 4) {
            engine.setVariable("console_model", args[1]);
            engine.setVariable("console_firmware", args[2]);
        } else if (addr.startsWith("/ch/") && addr.endsWith("/mix/fader")) {
            // e.g. /ch/01/mix/fader [0.75]
            var ch = addr.split("/")[2];
            var faderVal = (args[0] * 100).toFixed(0);
            engine.setVariable("ch_" + ch + "_fader", faderVal);
        } else if (addr.startsWith("/ch/") && addr.endsWith("/mix/on")) {
            // e.g. /ch/01/mix/on [1 = unmuted, 0 = muted]
            var ch = addr.split("/")[2];
            var isMuted = args[0] === 0 ? "true" : "false";
            engine.setVariable("ch_" + ch + "_muted", isMuted);
        }
    },
    
    onAction: function(transport, actionId, params) {
        var ch = params.channel.padStart(2, "0");
        
        if (actionId === "set_fader") {
            var floatVal = parseFloat(params.level) / 100.0;
            var packet = engine.osc.encode("/ch/" + ch + "/mix/fader", [floatVal]);
            transport.sendBytes(packet);
            return "Set Ch " + ch + " fader to " + params.level + "%";
        } else if (actionId === "toggle_mute") {
            var currMuted = engine.getVariable("ch_" + ch + "_muted") === "true";
            var nextOnVal = currMuted ? 1 : 0;
            var packet = engine.osc.encode("/ch/" + ch + "/mix/on", [nextOnVal]);
            transport.sendBytes(packet);
            return "Toggled mute on Ch " + ch;
        }
        return "Unknown action";
    },
    
    onHeartbeat: function(transport) {
        // Send /xremote keepalive to keep live metering subscriptions active
        var remotePacket = engine.osc.encode("/xremote", []);
        transport.sendBytes(remotePacket);
    }
};
```
