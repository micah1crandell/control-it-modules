#!/usr/bin/env python3
"""
Control-It Wi-Fi Developer Bridge & MCP Server (Zero-Dependency)
================================================================
Bridges AI Coding Agents (Antigravity, Claude Desktop, Cursor, Windsurf) directly
to a running Control-It iOS/iPadOS/macOS app over local Wi-Fi.

Supports two execution modes:
1. Standard MCP Server (JSON-RPC 2.0 over stdio) — default when invoked without arguments.
2. Direct CLI Tool — when invoked with CLI subcommands:
   - python3 control_it_mcp.py status [--host IP] [--port 8080]
   - python3 control_it_mcp.py list-modules
   - python3 control_it_mcp.py deploy <path/to/module.json>
   - python3 control_it_mcp.py test-action <module_id> <action_id> ['{"param":"val"}']
   - python3 control_it_mcp.py simulate-packet <module_id> --text "%1POWR=1\r"
   - python3 control_it_mcp.py simulate-packet <module_id> --hex "81 01 04 00 02 FF"
   - python3 control_it_mcp.py variables <module_id>
   - python3 control_it_mcp.py logs <module_id>
"""

import os
import sys
import json
import urllib.request
import urllib.error
import argparse

DEFAULT_HOST = os.environ.get("CONTROLIT_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("CONTROLIT_PORT", "8080"))
DEFAULT_PIN = os.environ.get("CONTROLIT_PIN", "")


def api_request(method, path, body=None, host=DEFAULT_HOST, port=DEFAULT_PORT, pin=DEFAULT_PIN):
    url = f"http://{host}:{port}{path}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if pin:
        headers["Authorization"] = f"Bearer {pin}"
        headers["X-ControlIt-Pin"] = str(pin)

    data = None
    if body is not None:
        if isinstance(body, (dict, list)):
            data = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            data = body.encode("utf-8")
        elif isinstance(body, bytes):
            data = body

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": raw}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(err_body)
        except Exception:
            return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        return {
            "error": f"Failed to reach Control-It at {url}: {e}. Ensure Control-It HTTP Server is running on your device and CONTROLIT_HOST is set."
        }


# ============================================================================
# MCP Server Tool Definitions (JSON-RPC 2.0 over stdio)
# ============================================================================

MCP_TOOLS = [
    {
        "name": "controlit_status",
        "description": "Checks connection health and device status of the running Control-It iOS/iPadOS app over Wi-Fi.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Optional device IP address (defaults to CONTROLIT_HOST or 127.0.0.1)"},
                "port": {"type": "integer", "description": "Optional HTTP port (defaults to 8080)"}
            }
        }
    },
    {
        "name": "controlit_list_modules",
        "description": "Lists all community and custom hardware modules currently installed on the Control-It device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer"}
            }
        }
    },
    {
        "name": "controlit_get_module",
        "description": "Retrieves the complete JSON definition and JavaScript driver script for a specific module ID from the device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleId": {"type": "string", "description": "The module ID to inspect (e.g. 'blackmagic_atem', 'obs_studio')"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleId"]
        }
    },
    {
        "name": "controlit_deploy_module",
        "description": "Hot-deploys a new or updated CompanionModule JSON (with driverScript, actions, variables, and dynamicColorRules) directly into the user's running Control-It app over Wi-Fi.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleJson": {
                    "type": "string",
                    "description": "Complete JSON string of the CompanionModule, or path to a local .json file."
                },
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleJson"]
        }
    },
    {
        "name": "controlit_test_action",
        "description": "Remotely executes a module action inside Control-It's JavaScriptCore runtime on the device and returns the action result, execution time, mutated variables, and emitted packet logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleId": {"type": "string", "description": "Target module ID"},
                "actionId": {"type": "string", "description": "Action ID to execute"},
                "params": {"type": "object", "description": "Action input parameters dictionary"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleId", "actionId"]
        }
    },
    {
        "name": "controlit_simulate_packet",
        "description": "Injects a simulated inbound hardware packet (ASCII text or hex bytes) into the module's onMessage handler on the device to verify telemetry parsing and variable updates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleId": {"type": "string", "description": "Target module ID"},
                "text": {"type": "string", "description": "Optional UTF-8/ASCII string packet to inject (e.g. '%1POWR=1\\r')"},
                "hex": {"type": "string", "description": "Optional raw hex string packet to inject (e.g. '81 01 04 00 02 FF')"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleId"]
        }
    },
    {
        "name": "controlit_get_variables",
        "description": "Returns all live dynamic variables currently set by a module on the Control-It device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleId": {"type": "string", "description": "Target module ID"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleId"]
        }
    },
    {
        "name": "controlit_get_logs",
        "description": "Retrieves recent JavaScript driver logs, warnings, errors, and sent/received packet traces for a module.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "moduleId": {"type": "string", "description": "Target module ID"},
                "host": {"type": "string"},
                "port": {"type": "integer"}
            },
            "required": ["moduleId"]
        }
    }
]


def handle_tool_call(name, args):
    host = args.get("host") or DEFAULT_HOST
    port = int(args.get("port") or DEFAULT_PORT)

    if name == "controlit_status":
        return api_request("GET", "/api/v1/health", host=host, port=port)

    elif name == "controlit_list_modules":
        return api_request("GET", "/api/v1/modules", host=host, port=port)

    elif name == "controlit_get_module":
        mod_id = args["moduleId"]
        return api_request("GET", f"/api/v1/modules/{mod_id}", host=host, port=port)

    elif name == "controlit_deploy_module":
        mod_input = args["moduleJson"]
        if os.path.exists(mod_input):
            with open(mod_input, "r", encoding="utf-8") as f:
                mod_input = f.read()
        return api_request("POST", "/api/v1/modules", body=mod_input, host=host, port=port)

    elif name == "controlit_test_action":
        mod_id = args["moduleId"]
        payload = {
            "actionId": args["actionId"],
            "params": args.get("params", {})
        }
        return api_request("POST", f"/api/v1/modules/{mod_id}/test-action", body=payload, host=host, port=port)

    elif name == "controlit_simulate_packet":
        mod_id = args["moduleId"]
        payload = {}
        if "text" in args and args["text"] is not None:
            payload["text"] = args["text"]
        if "hex" in args and args["hex"] is not None:
            payload["hex"] = args["hex"]
        return api_request("POST", f"/api/v1/modules/{mod_id}/simulate-packet", body=payload, host=host, port=port)

    elif name == "controlit_get_variables":
        mod_id = args["moduleId"]
        return api_request("GET", f"/api/v1/modules/{mod_id}/variables", host=host, port=port)

    elif name == "controlit_get_logs":
        mod_id = args["moduleId"]
        return api_request("GET", f"/api/v1/modules/{mod_id}/logs", host=host, port=port)

    return {"error": f"Unknown tool: {name}"}


def run_mcp_stdio_loop():
    """Runs standard Model Context Protocol JSON-RPC 2.0 loop over stdin/stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "control-it-mcp",
                        "version": "2.2.0"
                    }
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": MCP_TOOLS}
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result_obj = handle_tool_call(tool_name, tool_args)
            is_error = "error" in result_obj and not result_obj.get("success", False)
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_obj, indent=2)
                        }
                    ],
                    "isError": is_error
                }
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()

        elif msg_id is not None:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {}
            }
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


def run_cli():
    parser = argparse.ArgumentParser(description="Control-It Wi-Fi Developer Bridge CLI & MCP Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Control-It device IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Control-It HTTP server port")
    parser.add_argument("--pin", default=DEFAULT_PIN, help="Optional Developer Bridge PIN")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="Check device health and bridge status")
    subparsers.add_parser("list-modules", help="List all installed modules on device")

    get_p = subparsers.add_parser("get-module", help="Export module JSON by ID")
    get_p.add_argument("module_id")

    dep_p = subparsers.add_parser("deploy", help="Hot-deploy a module JSON file to the device")
    dep_p.add_argument("file", help="Path to module .json file")

    act_p = subparsers.add_parser("test-action", help="Execute a module action on the device")
    act_p.add_argument("module_id")
    act_p.add_argument("action_id")
    act_p.add_argument("params_json", nargs="?", default="{}", help="JSON object of action parameters")

    sim_p = subparsers.add_parser("simulate-packet", help="Inject mock hardware packet into onMessage")
    sim_p.add_argument("module_id")
    sim_p.add_argument("--text", help="UTF-8 text payload")
    sim_p.add_argument("--hex", help="Hex byte string payload")

    var_p = subparsers.add_parser("variables", help="Inspect current variables for a module")
    var_p.add_argument("module_id")

    log_p = subparsers.add_parser("logs", help="Fetch recent driver logs for a module")
    log_p.add_argument("module_id")

    args = parser.parse_args()

    if args.command == "status":
        res = api_request("GET", "/api/v1/health", host=args.host, port=args.port, pin=args.pin)
    elif args.command == "list-modules":
        res = api_request("GET", "/api/v1/modules", host=args.host, port=args.port, pin=args.pin)
    elif args.command == "get-module":
        res = api_request("GET", f"/api/v1/modules/{args.module_id}", host=args.host, port=args.port, pin=args.pin)
    elif args.command == "deploy":
        with open(args.file, "r", encoding="utf-8") as f:
            body = f.read()
        res = api_request("POST", "/api/v1/modules", body=body, host=args.host, port=args.port, pin=args.pin)
    elif args.command == "test-action":
        params = json.loads(args.params_json)
        res = api_request(
            "POST",
            f"/api/v1/modules/{args.module_id}/test-action",
            body={"actionId": args.action_id, "params": params},
            host=args.host,
            port=args.port,
            pin=args.pin
        )
    elif args.command == "simulate-packet":
        payload = {}
        if args.text is not None:
            payload["text"] = args.text
        if args.hex is not None:
            payload["hex"] = args.hex
        res = api_request(
            "POST",
            f"/api/v1/modules/{args.module_id}/simulate-packet",
            body=payload,
            host=args.host,
            port=args.port,
            pin=args.pin
        )
    elif args.command == "variables":
        res = api_request("GET", f"/api/v1/modules/{args.module_id}/variables", host=args.host, port=args.port, pin=args.pin)
    elif args.command == "logs":
        res = api_request("GET", f"/api/v1/modules/{args.module_id}/logs", host=args.host, port=args.port, pin=args.pin)
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_mcp_stdio_loop()
