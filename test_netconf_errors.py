#!/usr/bin/env python3
import sys
from ncclient import manager
from ncclient.operations.rpc import RPCError

DEVICE_PARAMS = {
    'host': '10.1.1.2',                 # Replace with your NETCONF-enabled device IP
    'port': 830,
    'username': 'admin',                # Replace with your NETCONF-enabled device username
    'password': 'SuperSecretPassword',  # Replace with your NETCONF-enabled device password
    'hostkey_verify': False,
    'device_params': {'name': 'iosxe'},
    'timeout': 30
}

# --- PAYLOAD 1: Schema / Type Error (Customer's failure scenario) ---
# 'name' is string, but MTU or name formatted with illegal XML tag / bad type
SCHEMA_ERROR_PAYLOAD = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <Loopback>
        <name>91</name>
        <description>Test Loopback 91 - Valid</description>
      </Loopback>
      <Loopback>
        <name>INVALID_NAME_NOT_AN_INTEGER</name>
        <description>Test Loopback 92 - Schema Violation</description>
      </Loopback>
    </interface>
  </native>
</config>
"""

# --- PAYLOAD 2: Semantic / Runtime Error (Duplicate IP Conflict) ---
SEMANTIC_CONFLICT_PAYLOAD = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <Loopback>
        <name>91</name>
        <description>Test Loopback 91 - Valid</description>
        <ip>
          <address>
            <primary>
              <address>192.168.99.1</address>
              <mask>255.255.255.0</mask>
            </primary>
          </address>
        </ip>
      </Loopback>
      <Loopback>
        <name>92</name>
        <description>Test Loopback 92 - Overlapping Subnet Conflict</description>
        <ip>
          <address>
            <primary>
              <address>192.168.99.1</address>
              <mask>255.255.255.0</mask>
            </primary>
          </address>
        </ip>
      </Loopback>
    </interface>
  </native>
</config>
"""

def verify_interfaces(m):
    """Check running state of Loopback 91 and 92"""
    filter_xml = """
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
          <Loopback>
            <name>91</name>
          </Loopback>
          <Loopback>
            <name>92</name>
          </Loopback>
        </interface>
      </native>
    </filter>
    """
    res = m.get_config(source='running', filter=filter_xml)
    print("  [Running Config Check]:\n", res)

def cleanup(m):
    """Remove test loopbacks"""
    cleanup_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
        <interface>
          <Loopback operation="delete">
            <name>91</name>
          </Loopback>
          <Loopback operation="delete">
            <name>92</name>
          </Loopback>
        </interface>
      </native>
    </config>
    """
    try:
        m.edit_config(target='running', config=cleanup_xml)
    except Exception:
        pass

def run_tests():
    with manager.connect(**DEVICE_PARAMS) as m:
        print("Connected to IOS XE device via NETCONF.\n")

        # --- TEST 1 ---
        print("==================================================")
        print("TEST 1: Schema Violation with error_option='stop-on-error'")
        print("==================================================")
        cleanup(m)
        try:
            m.edit_config(target='running', config=SCHEMA_ERROR_PAYLOAD, error_option='stop-on-error')
            print("Result: Unexpected Success!")
        except RPCError as e:
            print(f"Result: RPC Error Caught as expected!\nError Tag: {e.tag}\nError Message: {e.message}")
        
        verify_interfaces(m)

        # --- TEST 2 ---
        print("\n==================================================")
        print("TEST 2: Semantic Conflict with error_option='stop-on-error'")
        print("==================================================")
        cleanup(m)
        try:
            m.edit_config(target='running', config=SEMANTIC_CONFLICT_PAYLOAD, error_option='stop-on-error')
            print("Result: Success (or partial)")
        except RPCError as e:
            print(f"Result: RPC Error Caught!\nError Tag: {e.tag}\nError Message: {e.message}")
        
        verify_interfaces(m)

        # --- Cleanup ---
        cleanup(m)
        print("\nTest run complete.")

if __name__ == '__main__':
    run_tests()
