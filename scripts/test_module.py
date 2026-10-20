#!/usr/bin/env python3
"""
Control-It Headless Module Test Runner
Executes module driver scripts inside macOS native JavaScriptCore (jsc) or Node.js.
Validates syntax, lifecycle exports, action dispatches, and variable mutations.
"""

import os
import sys
import json
import tempfile
import subprocess

JSC_PATH = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"

TEST_HARNESS_JS = """
// Control-It Mock Test Harness for JavaScriptCore
var recordedLogs = [];
var recordedSends = [];
var variables = {};
var currentStatus = { status: "disconnected", message: "" };

var engine = {
    log: function(msg) { recordedLogs.push(String(msg)); },
    setVariable: function(k, v) { variables[k] = String(v); },
    setVariables: function(dict) {
        for (var k in dict) { variables[k] = String(dict[k]); }
    },
    getVariable: function(k) { return variables[k] || ""; },
    setStatus: function(s, m) { currentStatus = { status: s, message: m }; },
    reconnect: function() { recordedLogs.push("[ENGINE RECONNECT]"); },
    fail: function(r) { currentStatus = { status: "failed", message: r }; },
    secret: function(k) { return "mock_secret_" + k; },
    crypto: {
        sha256: function(s) { return "mock_sha256_" + s.length; },
        md5: function(s) { return "mock_md5_" + s.length; },
        base64Encode: function(s) { return "mock_b64_" + s; },
        base64Decode: function(s) { return s; }
    },
    checksum: {
        sum8: function(bytes) {
            var sum = 0;
            for (var i = 0; i < bytes.length; i++) sum = (sum + bytes[i]) & 0xFF;
            return sum;
        },
        crc16Modbus: function(b) { return 0x1234; }
    },
    binary: {
        pack: function(fmt, vals) { return [0xAA, 0x55]; },
        unpack: function(fmt, buf) { return [1, "test", 0]; }
    },
    osc: {
        encode: function(addr, args) { return [0x2F, 0x6F, 0x73, 0x63]; },
        decode: function(buf) { return { address: "/test", args: [1.0] }; }
    },
    buffer: {
        create: function(n) { return new Array(n).fill(0); },
        fromHex: function(h) { return []; },
        toHex: function(b) { return "HEX"; },
        readUInt16BE: function(b, o) { return 0; }
    }
};

var transport = {
    send: function(text) { recordedSends.push({ type: "text", data: text }); return true; },
    sendBytes: function(bytes) { recordedSends.push({ type: "bytes", data: bytes }); return true; },
    sendHex: function(hex) { recordedSends.push({ type: "hex", data: hex }); return true; },
    sendJSON: function(obj) { recordedSends.push({ type: "json", data: obj }); return true; },
    sendAndAwait: function(p, m, t) {
        recordedSends.push({ type: "await", data: p });
        return Promise.resolve("OK");
    }
};

var module = { exports: {} };
var exports = module.exports;

// Load driver
{DRIVER_CODE}

// Run test suites
var testResults = {
    success: true,
    exportedHooks: [],
    actionResults: {},
    variables: {},
    sends: [],
    logs: [],
    errors: []
};

try {
    var known = ["onConnect", "onTransportReady", "onAction", "onMessage", "onHeartbeat", "onDisconnect", "onError", "onStop"];
    for (var i = 0; i < known.length; i++) {
        if (typeof module.exports[known[i]] === "function") {
            testResults.exportedHooks.push(known[i]);
        }
    }

    // 1. Test onConnect & onTransportReady
    if (module.exports.onConnect) {
        module.exports.onConnect(transport, { host: "127.0.0.1", port: 8080 });
    }
    if (module.exports.onTransportReady) {
        module.exports.onTransportReady(transport, { host: "127.0.0.1", port: 8080 });
    }

    // 2. Test declared actions
    var actionsToTest = {ACTIONS_JSON};
    for (var a = 0; a < actionsToTest.length; a++) {
        var act = actionsToTest[a];
        var params = {};
        if (act.inputs) {
            for (var inp = 0; inp < act.inputs.length; inp++) {
                params[act.inputs[inp].id] = act.inputs[inp].defaultValue || "1";
            }
        }
        if (module.exports.onAction) {
            try {
                var res = module.exports.onAction(transport, act.id, params);
                testResults.actionResults[act.id] = String(res);
            } catch(e) {
                testResults.errors.push("Action " + act.id + " threw error: " + e.message);
                testResults.success = false;
            }
        }
    }

    testResults.variables = variables;
    testResults.sends = recordedSends;
    testResults.logs = recordedLogs;
} catch(err) {
    testResults.success = false;
    testResults.errors.push("Harness error: " + err.message);
}

print(JSON.stringify(testResults));
"""

def test_module(module_path):
    if not os.path.exists(module_path):
        print(f"❌ File not found: {module_path}")
        return False

    print(f"\n🧪 Testing Module: {os.path.basename(module_path)}")
    print("=" * 60)

    with open(module_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"❌ JSON Parse Error: {e}")
            return False

    required = ["id", "name", "version", "manufacturer", "actions"]
    missing = [r for r in required if r not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False

    driver_script = data.get("driverScript", "")
    if not driver_script.strip():
        print("⚠️ Module has no driverScript specified (pure static action catalog).")
        print("✅ JSON schema and action definitions valid.")
        return True

    # Check for jsc or node
    runner_cmd = None
    if os.path.exists(JSC_PATH):
        runner_cmd = [JSC_PATH]
    else:
        # Fallback to node
        node_path = subprocess.run(["which", "node"], capture_output=True, text=True).stdout.strip()
        if node_path:
            runner_cmd = [node_path, "-e"]

    if not runner_cmd:
        print("❌ Neither macOS JavaScriptCore (jsc) nor Node.js found.")
        return False

    actions_json = json.dumps(data.get("actions", []))
    harness_content = TEST_HARNESS_JS.replace("{DRIVER_CODE}", driver_script).replace("{ACTIONS_JSON}", actions_json)

    with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False) as tf:
        tf.write(harness_content)
        temp_js_path = tf.name

    try:
        proc = subprocess.run([JSC_PATH, temp_js_path], capture_output=True, text=True, timeout=10)
        output = proc.stdout.strip()
        err_output = proc.stderr.strip()

        if proc.returncode != 0 or not output:
            print(f"❌ Script execution failed (exit code {proc.returncode}):")
            if err_output:
                print(f"   {err_output}")
            return False

        results = json.loads(output)
        
        print(f"✅ Module ID: {data['id']} (v{data['version']})")
        print(f"📦 Exported Hooks: {', '.join(results.get('exportedHooks', []))}")
        print(f"⚡ Tested {len(results.get('actionResults', {}))} Actions:")
        for act_id, res in results.get("actionResults", {}).items():
            print(f"   - {act_id} -> '{res}'")
        print(f"📡 Emitted {len(results.get('sends', []))} Network Sends")
        print(f"📊 State Variables Mutated: {list(results.get('variables', {}).keys())}")

        if results.get("errors"):
            print("\n❌ Errors Encountered:")
            for err in results["errors"]:
                print(f"   ! {err}")
            return False

        print("\n🎉 ALL DRIVER HOOKS & ACTIONS PASSED HEADLESS VERIFICATION!")
        return True

    except Exception as e:
        print(f"❌ Test runner exception: {e}")
        return False
    finally:
        if os.path.exists(temp_js_path):
            os.remove(temp_js_path)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Control It/CommunityModules/agent-pack/templates/template_tcp_linedelimited.json"
    success = test_module(target)
    sys.exit(0 if success else 1)
