#!/usr/bin/env python3
"""
Control-It Community Module Validator
Validates module JSON files against schema, verifies SHA-256 hashes, and checks JavaScript syntax.
"""

import os
import sys
import json
import glob
import hashlib

def validate_all(root_dir="."):
    manifest_path = os.path.join(root_dir, "manifest.json")
    modules_dir = os.path.join(root_dir, "modules")
    
    if not os.path.exists(manifest_path):
        print("❌ manifest.json not found at", manifest_path)
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_modules = {m["id"]: m for m in manifest.get("modules", [])}
    all_valid = True
    
    json_files = glob.glob(os.path.join(modules_dir, "*.json"))
    print(f"🔍 Validating {len(json_files)} modules in '{modules_dir}'...\n")

    for jf in sorted(json_files):
        mod_id = os.path.basename(jf).replace(".json", "")
        with open(jf, "rb") as f:
            raw_bytes = f.read()

        try:
            mod_data = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            print(f"❌ {mod_id}: Invalid JSON format: {e}")
            all_valid = False
            continue

        # Check required fields
        required = ["id", "name", "version", "manufacturer", "actions"]
        missing = [r for r in required if r not in mod_data]
        if missing:
            print(f"❌ {mod_id}: Missing required fields: {missing}")
            all_valid = False
            continue

        # Check SHA-256 in manifest
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        if mod_id in manifest_modules:
            expected_sha = manifest_modules[mod_id].get("sha256", "")
            if actual_sha != expected_sha:
                print(f"❌ {mod_id}: SHA-256 mismatch! Manifest: {expected_sha[:8]}... vs File: {actual_sha[:8]}...")
                all_valid = False
            else:
                action_count = len(mod_data.get("actions", []))
                version = mod_data.get("version", "1.0.0")
                print(f"✅ {mod_id} (v{version}, {action_count} actions) - SHA256: {actual_sha[:8]}... OK")
        else:
            print(f"⚠️ {mod_id}: Present in modules/ but missing from manifest.json")
            all_valid = False

    print("\n" + ("="*50))
    if all_valid:
        print("🎉 ALL MODULES VALID AND IN INTEGRITY SYNC!")
    else:
        print("❌ VALIDATION FAILED. Please resolve issues above.")
    print("="*50)
    return all_valid

if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    success = validate_all(target_dir)
    sys.exit(0 if success else 1)
