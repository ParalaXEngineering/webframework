"""
Configuration Manager Module

Handles configuration file operations and network interface management.
Extracted from settings.py to separate business logic from presentation layer.
"""

import subprocess
import platform
from typing import Tuple, Optional


def apply_network_config(interface: str, ip_type: str, ip_address: Optional[str] = None, 
                        subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                        dns: Optional[str] = None) -> Tuple[bool, str]:
    """
    Apply network configuration to a network interface.
    
    Args:
        interface: Network interface name
        ip_type: Either "Static" or "DHCP"
        ip_address: Static IP address (required for Static)
        subnet_mask: Subnet mask (required for Static)
        gateway: Default gateway (optional)
        dns: DNS server (optional)
        
    Returns:
        Tuple of (success: bool, message: str)
        
    Example:
        >>> success, msg = apply_network_config("eth0", "Static", "192.168.1.100", "255.255.255.0")
    """
    try:
        if platform.system() == "Windows":
            return _apply_windows_config(interface, ip_type, ip_address, subnet_mask, gateway, dns)
        else:
            return _apply_linux_config(interface, ip_type, ip_address, subnet_mask, gateway, dns)
    except Exception as e:
        return False, f"Configuration error: {str(e)}"


def _apply_windows_config(interface: str, ip_type: str, ip_address: Optional[str] = None,
                          subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                          dns: Optional[str] = None) -> Tuple[bool, str]:
    """Apply network configuration on Windows systems."""
    commands = []
    
    if ip_type == "DHCP":
        commands.append(f'netsh interface ip set address name="{interface}" dhcp')
        commands.append(f'netsh interface ip set dns name="{interface}" dhcp')
    else:  # Static
        if not ip_address or not subnet_mask:
            return False, "IP address and subnet mask are required for static configuration"
        
        cmd = f'netsh interface ip set address name="{interface}" static {ip_address} {subnet_mask}'
        if gateway:
            cmd += f' {gateway}'
        commands.append(cmd)
        
        if dns:
            commands.append(f'netsh interface ip set dns name="{interface}" static {dns}')
    
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Command failed: {result.stderr}"
    
    return True, "Network configuration applied successfully"


def _apply_linux_config(interface: str, ip_type: str, ip_address: Optional[str] = None,
                       subnet_mask: Optional[str] = None, gateway: Optional[str] = None, 
                       dns: Optional[str] = None) -> Tuple[bool, str]:
    """Apply network configuration on Linux systems."""
    commands = []
    
    if ip_type == "DHCP":
        commands.append(f'dhclient {interface}')
    else:  # Static
        if not ip_address or not subnet_mask:
            return False, "IP address and subnet mask are required for static configuration"
        
        commands.append(f'ip addr flush dev {interface}')
        commands.append(f'ip addr add {ip_address}/{subnet_mask} dev {interface}')
        
        if gateway:
            commands.append(f'ip route add default via {gateway}')
        
        if dns:
            with open('/etc/resolv.conf', 'w') as f:
                f.write(f'nameserver {dns}\n')
    
    for cmd in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            return False, f"Command failed: {result.stderr}"
    
    return True, "Network configuration applied successfully"
