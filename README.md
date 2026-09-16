# cisco-ios-xe-with-netconf
# Cisco IOS XE NETCONF `<edit-config>` Validation Test Script

## Overview

This test suite demonstrates how Cisco IOS XE validates and processes NETCONF `<edit-config>` requests:

* **Schema-Level Validation:** Verifies the XML payload against compiled YANG data models (checking data types, structure, allowed values, and mandatory fields).
* **Execution & Semantic Validation:** Verifies that the configuration commands can be accepted and applied by the device's operational subsystems.

Both tests demonstrate standard RFC 6241 error handling (`error-option='stop-on-error'`) and include automated post-execution datastore checks.

---

## Prerequisites

* **Python:** Python 3.8+
* **Dependencies:** `ncclient`
  ```bash
  pip install ncclient
  ```
* **Target Device Prerequisites (Cisco IOS XE):**
  * NETCONF-YANG enabled (`netconf-yang`)
  * User credentials with privilege 15 access

---

## Configuration: Parameters to Replace

Before running the script, update the device connection variables in the script header:

```python
# ==============================================================================
# DEVICE CONNECTION SETTINGS (REPLACE WITH YOUR TARGET LAB / DEVICE VALUES)
# ==============================================================================
ROUTER_HOST = "10.1.1.2"       # Replace with your switch/router IP or FQDN
ROUTER_PORT = 830              # Default NETCONF over SSH port (830)
ROUTER_USER = "admin"          # NETCONF username with privilege 15 access
ROUTER_PASS = "SuperSecretPassword"      # NETCONF user password
HOSTKEY_VERIFY = False         # Set to True in production environments
```

---

## Running the Script

Execute the script from your terminal:

```bash
python3 test_netconf_errors.py
```

---

## Understanding the Test Outputs

### Test 1: Schema Violation
* **What is tested:** The client sends an XML payload where a node expects an integer, but supplies a string value (`"INVALID_NAME_NOT_AN_INTEGER"`).
* **Where the error is caught:** Caught early during initial YANG schema validation before the device attempts configuration changes.
* **Expected Output:**
  ```text
  ==================================================
  TEST 1: Schema Violation with error_option='stop-on-error'
  Result: RPC Error Caught as expected!
  Error Tag: invalid-value
  Error Message: "INVALID_NAME_NOT_AN_INTEGER" is not a valid value.
  [Running Config Check]:
  <rpc-reply ...><data></data></rpc-reply>
  ```
* **Summary:** The device detects that the payload violates the defined YANG data type and rejects the RPC immediately. The running configuration remains completely unmodified (`<data></data>`).

---

### Test 2: Semantic / Execution Conflict
* **What is tested:** The XML structure and data types are fully valid according to the YANG model (passes schema validation), but the configuration cannot be applied by the device (e.g., conflicting feature parameters or an unsupported combination).
* **Where the error is caught:** Caught during configuration processing and application by the device subsystem.
* **Expected Output:**
  ```text
  ==================================================
  TEST 2: Semantic Conflict with error_option='stop-on-error'
  Result: RPC Error Caught!
  Error Tag: invalid-value
  Error Message: inconsistent value: Device refused one or more commands
  [Running Config Check]:
  <rpc-reply ...><data></data></rpc-reply>
  ```
* **Summary:** The device accepts the schema but encounters an operational conflict when applying the configuration. With `stop-on-error` configured, processing stops immediately upon encountering the issue and returns an `<rpc-error>`, ensuring no partial or corrupted configuration persists (`<data></data>`).
