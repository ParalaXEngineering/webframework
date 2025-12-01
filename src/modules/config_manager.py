"""Configuration Manager Module

Handles network interface configuration for Windows and Linux systems.
Extracted from settings.py to separate business logic from presentation layer.
"""

import logging
import platform
import subprocess
from typing import Optional, Tuple

# Framework modules - i18n
from .i18n.messages import (
    MSG_NETWORK_CONFIG_SUCCESS,
    ERROR_NETWORK_VALIDATION,
    ERROR_NETWORK_CONFIG,
    ERROR_NETWORK_CMD_FAILED,
)

# Domain-specific constants
IP_TYPE_STATIC = "Static"
IP_TYPE_DHCP = "DHCP"
PLATFORM_WINDOWS = "Windows"

logger = logging.getLogger(__name__)


def apply_network_config(interface: str, ip_type: str, ip_address: Optional[str] = None, 
                         subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                         dns: Optional[str] = None) -> Tuple[bool, str]:
     """Apply network configuration to a network interface.
     
     Args:
         interface: Network interface name.
         ip_type: Either "Static" (IP_TYPE_STATIC) or "DHCP" (IP_TYPE_DHCP).
         ip_address: Static IP address (required for Static configuration).
         subnet_mask: Subnet mask (required for Static configuration).
         gateway: Default gateway (optional).
         dns: DNS server (optional).
         
     Returns:
         Tuple of (success: bool, message: str).
         
     Example:
         >>> success, msg = apply_network_config("eth0", "Static", "192.168.1.100", "255.255.255.0")
     """
     try:
         if platform.system() == PLATFORM_WINDOWS:
             return _apply_windows_config(interface, ip_type, ip_address, subnet_mask, gateway, dns)
         return _apply_linux_config(interface, ip_type, ip_address, subnet_mask, gateway, dns)
     except Exception as e:
         logger.exception("Failed to apply network configuration for interface %s", interface)
         return False, ERROR_NETWORK_CONFIG.format(str(e))


def _apply_windows_config(interface: str, ip_type: str, ip_address: Optional[str] = None,
                          subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                          dns: Optional[str] = None) -> Tuple[bool, str]:
     """Apply network configuration on Windows systems using netsh commands."""
     commands = []
     
     if ip_type == IP_TYPE_DHCP:
         commands.append(f'netsh interface ip set address name="{interface}" dhcp')
         commands.append(f'netsh interface ip set dns name="{interface}" dhcp')
     elif ip_type == IP_TYPE_STATIC:
         if not ip_address or not subnet_mask:
             logger.warning("Static config missing required parameters for interface %s", interface)
             return False, ERROR_NETWORK_VALIDATION
         
         cmd = f'netsh interface ip set address name="{interface}" static {ip_address} {subnet_mask}'
         if gateway:
             cmd += f' {gateway}'
         commands.append(cmd)
         
         if dns:
             commands.append(f'netsh interface ip set dns name="{interface}" static {dns}')
     
     for cmd in commands:
         result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
         if result.returncode != 0:
             logger.error("Windows netsh command failed: %s", result.stderr)
             return False, ERROR_NETWORK_CMD_FAILED.format(result.stderr)
     
     logger.info("Network configuration applied successfully on Windows for %s", interface)
     return True, MSG_NETWORK_CONFIG_SUCCESS


def _apply_linux_config(interface: str, ip_type: str, ip_address: Optional[str] = None,
                        subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                        dns: Optional[str] = None) -> Tuple[bool, str]:
     """Apply network configuration on Linux systems using ip and dhclient commands."""
     commands = []
     
     if ip_type == IP_TYPE_DHCP:
         commands.append(f'dhclient {interface}')
     elif ip_type == IP_TYPE_STATIC:
         if not ip_address or not subnet_mask:
             logger.warning("Static config missing required parameters for interface %s", interface)
             return False, ERROR_NETWORK_VALIDATION
         
         commands.append(f'ip addr flush dev {interface}')
         commands.append(f'ip addr add {ip_address}/{subnet_mask} dev {interface}')
         
         if gateway:
             commands.append(f'ip route add default via {gateway}')
         
         if dns:
             commands.append(f'echo "nameserver {dns}" > /etc/resolv.conf')
     
     for cmd in commands:
         result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
         if result.returncode != 0:
             logger.error("Linux command failed: %s", result.stderr)
             return False, ERROR_NETWORK_CMD_FAILED.format(result.stderr)
     
     logger.info("Network configuration applied successfully on Linux for %s", interface)
     return True, MSG_NETWORK_CONFIG_SUCCESS
