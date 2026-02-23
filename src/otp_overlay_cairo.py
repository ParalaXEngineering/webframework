#!/usr/bin/env python3
"""
OTP Overlay using Cairo + Pango for proper font rendering.

Uses Cairo for graphics and Pango for text with TrueType font support.
This allows rendering text at any size with the Liberation Sans font.
"""
import os
import sys
import time
import ctypes
import ctypes.util
import logging
import argparse
from pathlib import Path
from typing import Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("otp_cairo")

# OTP file configuration
OTP_BASE_PATH = "/var/lib/dfnet"
OTP_SUBDIR = "oufnis"
OTP_FILENAME = "otp_secret"
OTP_TIMESTAMP_FILENAME = "otp_timestamp"
OTP_VALIDITY_SECONDS = 30
AUTH_SIGNAL_FILENAME = "auth_active"
POLL_INTERVAL = 1.0
AUTH_SIGNAL_TIMEOUT = 5.0  # Must be > heartbeat interval (2s)

# X11 connection retry configuration (for slow startup after reboot)
X11_MAX_RETRIES = 30  # Max attempts to connect to X11
X11_RETRY_DELAY = 2.0  # Seconds between retries


def get_target_type() -> str:
    """Determine target type from hostname."""
    return "hmi"


def get_otp_file_path() -> Path:
    """Get the path to the OTP secret file."""
    target_type = get_target_type()
    return Path(OTP_BASE_PATH) / target_type / OTP_SUBDIR / OTP_FILENAME


def get_otp_timestamp_path() -> Path:
    """Get the path to the OTP timestamp file."""
    target_type = get_target_type()
    return Path(OTP_BASE_PATH) / target_type / OTP_SUBDIR / OTP_TIMESTAMP_FILENAME


def read_otp_timestamp() -> float:
    """Read the OTP creation timestamp."""
    try:
        ts_path = get_otp_timestamp_path()
        if ts_path.exists():
            return float(ts_path.read_text().strip())
    except Exception as e:
        logger.error(f"Error reading timestamp: {e}")
    return 0.0


def get_otp_time_remaining() -> int:
    """Get remaining validity time for current OTP in seconds."""
    created_at = read_otp_timestamp()
    if created_at == 0:
        return 0
    elapsed = time.time() - created_at
    remaining = OTP_VALIDITY_SECONDS - elapsed
    return max(0, int(remaining))


def read_otp_code() -> Optional[str]:
    """Read the current OTP code from file."""
    otp_path = get_otp_file_path()
    try:
        if otp_path.exists():
            code = otp_path.read_text().strip()
            if code and len(code) == 6 and code.isdigit():
                return code
    except Exception as e:
        logger.error(f"Error reading OTP: {e}")
    return None


def get_auth_signal_path() -> Path:
    """Get the path to the auth activity signal file."""
    target_type = get_target_type()
    return Path(OTP_BASE_PATH) / target_type / OTP_SUBDIR / AUTH_SIGNAL_FILENAME


def clear_auth_signal():
    """Clear the auth signal file at startup to prevent stale signals."""
    signal_path = get_auth_signal_path()
    try:
        if signal_path.exists():
            signal_path.write_text("0")
            logger.info(f"Cleared auth signal at startup: {signal_path}")
    except Exception as e:
        logger.warning(f"Failed to clear auth signal: {e}")


def is_auth_page_active() -> bool:
    """Check if someone is currently on the auth page."""
    signal_path = get_auth_signal_path()
    try:
        if not signal_path.exists():
            return False
        content = signal_path.read_text().strip()
        if not content or content == "0":
            return False
        signal_timestamp = float(content)
        age = time.time() - signal_timestamp
        return age < AUTH_SIGNAL_TIMEOUT
    except (ValueError, OSError) as e:
        logger.debug(f"Error reading auth signal: {e}")
        return False


# ============================================================================
# Load libraries
# ============================================================================

def _load_libs():
    """Load X11, Cairo, and Pango libraries."""
    libs = {}
    
    # X11
    x11_path = ctypes.util.find_library('X11')
    if not x11_path:
        raise RuntimeError("libX11 not found")
    libs['x11'] = ctypes.CDLL(x11_path)
    
    # Cairo
    cairo_path = ctypes.util.find_library('cairo')
    if not cairo_path:
        raise RuntimeError("libcairo not found")
    libs['cairo'] = ctypes.CDLL(cairo_path)
    
    # Pango
    pango_path = ctypes.util.find_library('pango-1.0')
    if not pango_path:
        raise RuntimeError("libpango not found")
    libs['pango'] = ctypes.CDLL(pango_path)
    
    # PangoCairo
    pangocairo_path = ctypes.util.find_library('pangocairo-1.0')
    if not pangocairo_path:
        raise RuntimeError("libpangocairo not found")
    libs['pangocairo'] = ctypes.CDLL(pangocairo_path)
    
    return libs


# ============================================================================
# X11 structures
# ============================================================================

class Display(ctypes.Structure):
    pass

class Visual(ctypes.Structure):
    pass

class XSetWindowAttributes(ctypes.Structure):
    _fields_ = [
        ('background_pixmap', ctypes.c_ulong),
        ('background_pixel', ctypes.c_ulong),
        ('border_pixmap', ctypes.c_ulong),
        ('border_pixel', ctypes.c_ulong),
        ('bit_gravity', ctypes.c_int),
        ('win_gravity', ctypes.c_int),
        ('backing_store', ctypes.c_int),
        ('backing_planes', ctypes.c_ulong),
        ('backing_pixel', ctypes.c_ulong),
        ('save_under', ctypes.c_int),
        ('event_mask', ctypes.c_long),
        ('do_not_propagate_mask', ctypes.c_long),
        ('override_redirect', ctypes.c_int),
        ('colormap', ctypes.c_ulong),
        ('cursor', ctypes.c_ulong),
    ]

class XEvent(ctypes.Structure):
    _fields_ = [('type', ctypes.c_int), ('pad', ctypes.c_long * 24)]

# X11 constants
CWBackPixel = (1 << 1)
CWBorderPixel = (1 << 3)
CWOverrideRedirect = (1 << 9)
CWEventMask = (1 << 11)
ExposureMask = (1 << 15)
InputOutput = 1
Expose = 12


class CairoOverlay:
    """
    OTP overlay using Cairo + Pango for proper font rendering.
    """
    
    def __init__(self, position: str = "center", font_size: int = 20):
        self.position = position
        self.font_size = font_size
        self.current_otp: Optional[str] = None
        self.window_visible = False
        
        # Window dimensions (specs: 1200x180)
        self.width = 1200
        self.height = 180
        
        # X11 handles
        self.display = None
        self.window = None
        self.screen = 0
        
        # Cairo handles
        self.surface = None
        self.cr = None
        self.layout = None
        
        # Libraries loaded lazily in run()
        self.libs = None
    
    def _init_libs(self) -> bool:
        """Initialize libraries with error handling."""
        try:
            self.libs = _load_libs()
            self._setup_functions()
            return True
        except Exception as e:
            logger.warning(f"Failed to load libraries: {e}")
            return False
    
    def _setup_functions(self):
        """Setup ctypes function signatures."""
        x11 = self.libs['x11']
        cairo = self.libs['cairo']
        pango = self.libs['pango']
        pangocairo = self.libs['pangocairo']
        
        # X11 functions
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.POINTER(Display)
        
        x11.XDefaultScreen.argtypes = [ctypes.POINTER(Display)]
        x11.XDefaultScreen.restype = ctypes.c_int
        
        x11.XDisplayWidth.argtypes = [ctypes.POINTER(Display), ctypes.c_int]
        x11.XDisplayWidth.restype = ctypes.c_int
        
        x11.XDisplayHeight.argtypes = [ctypes.POINTER(Display), ctypes.c_int]
        x11.XDisplayHeight.restype = ctypes.c_int
        
        x11.XRootWindow.argtypes = [ctypes.POINTER(Display), ctypes.c_int]
        x11.XRootWindow.restype = ctypes.c_ulong
        
        x11.XCreateWindow.argtypes = [
            ctypes.POINTER(Display), ctypes.c_ulong,
            ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
            ctypes.c_uint, ctypes.c_int, ctypes.c_uint,
            ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(XSetWindowAttributes)
        ]
        x11.XCreateWindow.restype = ctypes.c_ulong
        
        x11.XMapWindow.argtypes = [ctypes.POINTER(Display), ctypes.c_ulong]
        x11.XUnmapWindow.argtypes = [ctypes.POINTER(Display), ctypes.c_ulong]
        x11.XRaiseWindow.argtypes = [ctypes.POINTER(Display), ctypes.c_ulong]
        x11.XFlush.argtypes = [ctypes.POINTER(Display)]
        x11.XPending.argtypes = [ctypes.POINTER(Display)]
        x11.XPending.restype = ctypes.c_int
        x11.XNextEvent.argtypes = [ctypes.POINTER(Display), ctypes.POINTER(XEvent)]
        x11.XCloseDisplay.argtypes = [ctypes.POINTER(Display)]
        x11.XDefaultVisual.argtypes = [ctypes.POINTER(Display), ctypes.c_int]
        x11.XDefaultVisual.restype = ctypes.c_void_p
        
        # Cairo functions
        cairo.cairo_xlib_surface_create.argtypes = [
            ctypes.POINTER(Display), ctypes.c_ulong, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_int
        ]
        cairo.cairo_xlib_surface_create.restype = ctypes.c_void_p
        
        cairo.cairo_create.argtypes = [ctypes.c_void_p]
        cairo.cairo_create.restype = ctypes.c_void_p
        
        cairo.cairo_set_source_rgb.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        cairo.cairo_set_source_rgba.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        cairo.cairo_rectangle.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
        cairo.cairo_fill.argtypes = [ctypes.c_void_p]
        cairo.cairo_move_to.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
        cairo.cairo_surface_flush.argtypes = [ctypes.c_void_p]
        cairo.cairo_destroy.argtypes = [ctypes.c_void_p]
        cairo.cairo_surface_destroy.argtypes = [ctypes.c_void_p]
        
        # Pango functions
        pango.pango_font_description_from_string.argtypes = [ctypes.c_char_p]
        pango.pango_font_description_from_string.restype = ctypes.c_void_p
        pango.pango_font_description_free.argtypes = [ctypes.c_void_p]
        pango.pango_layout_set_font_description.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        pango.pango_layout_set_text.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        pango.pango_layout_get_pixel_size.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        
        # PangoCairo functions
        pangocairo.pango_cairo_create_layout.argtypes = [ctypes.c_void_p]
        pangocairo.pango_cairo_create_layout.restype = ctypes.c_void_p
        pangocairo.pango_cairo_show_layout.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    
    def _get_window_position(self) -> Tuple[int, int]:
        """Calculate window position.
        
        Position specs: X=0, Y=350 from screen center
        (0,0 is screen center, Y positive = above center)
        """
        x11 = self.libs['x11']
        screen_width = x11.XDisplayWidth(self.display, self.screen)
        screen_height = x11.XDisplayHeight(self.display, self.screen)
        
        # Center of screen
        screen_center_x = screen_width // 2
        screen_center_y = screen_height // 2
        
        # Widget position: centered horizontally (X=0), Y=350 ABOVE center
        center_x = screen_center_x - (self.width // 2)  # X=0 means centered
        center_y = screen_center_y - 350 - (self.height // 2)  # Y=350 above center
        
        positions = {
            "center": (center_x, center_y),
            "top-left": (20, 20),
            "top-right": (screen_width - self.width - 20, 20),
            "bottom-left": (20, screen_height - self.height - 20),
            "bottom-right": (screen_width - self.width - 20, screen_height - self.height - 20),
        }
        return positions.get(self.position, positions["center"])
    
    def _init_display(self) -> bool:
        """Initialize X11 display."""
        x11 = self.libs['x11']
        
        display_name = os.environ.get('DISPLAY', ':0').encode('utf-8')
        self.display = x11.XOpenDisplay(display_name)
        if not self.display:
            logger.error(f"Cannot open display {display_name.decode()}")
            return False
        
        self.screen = x11.XDefaultScreen(self.display)
        return True
    
    def _create_window(self) -> bool:
        """Create the overlay window."""
        x11 = self.libs['x11']
        cairo = self.libs['cairo']
        
        x, y = self._get_window_position()
        root = x11.XRootWindow(self.display, self.screen)
        
        # Background color: 0xA0A0A0 (160, 160, 160) - will use Cairo for alpha
        bg_color = (160 << 16) | (160 << 8) | 160
        
        attrs = XSetWindowAttributes()
        attrs.background_pixel = bg_color
        attrs.border_pixel = bg_color
        attrs.override_redirect = 1
        attrs.event_mask = ExposureMask
        
        attr_mask = CWBackPixel | CWBorderPixel | CWOverrideRedirect | CWEventMask
        
        self.window = x11.XCreateWindow(
            self.display, root,
            x, y, self.width, self.height,
            0, 24, InputOutput, None, attr_mask, ctypes.byref(attrs)
        )
        
        if not self.window:
            logger.error("Failed to create window")
            return False
        
        # Create Cairo surface for the window
        visual = x11.XDefaultVisual(self.display, self.screen)
        self.surface = cairo.cairo_xlib_surface_create(
            self.display, self.window, visual, self.width, self.height
        )
        
        self.window_visible = False
        x11.XFlush(self.display)
        
        logger.info(f"Window created at ({x}, {y}), font_size={self.font_size}")
        return True
    
    def _draw(self):
        """Draw the OTP display using Cairo + Pango with countdown.
        
        Specs:
        - Background: 0xA0A0A0 (160,160,160) with 60% opacity (153/255)
        - Text: Open Sans, size 20, white (0xFFFFFFFF)
        """
        cairo = self.libs['cairo']
        pango = self.libs['pango']
        pangocairo = self.libs['pangocairo']
        
        # Get time remaining
        time_remaining = get_otp_time_remaining()
        
        # Create Cairo context
        cr = cairo.cairo_create(self.surface)
        
        # Clear entire surface first to prevent ghosting/remnants
        cairo.cairo_set_source_rgb(cr, 160/255, 160/255, 160/255)
        cairo.cairo_rectangle(cr, 0, 0, self.width, self.height)
        cairo.cairo_fill(cr)
        
        # Fill background: 0xA0A0A0 (160,160,160) with 60% opacity
        cairo.cairo_set_source_rgba(cr, 160/255, 160/255, 160/255, 153/255)
        cairo.cairo_rectangle(cr, 0, 0, self.width, self.height)
        cairo.cairo_fill(cr)
        
        # Draw progress bar background (darker, semi-transparent)
        bar_height = 12
        bar_y = self.height - bar_height - 20
        cairo.cairo_set_source_rgba(cr, 80/255, 80/255, 80/255, 0.8)
        cairo.cairo_rectangle(cr, 40, bar_y, self.width - 80, bar_height)
        cairo.cairo_fill(cr)
        
        # Draw progress bar (filled portion)
        if time_remaining > 0:
            progress_width = ((self.width - 80) * time_remaining) / OTP_VALIDITY_SECONDS
            # Color: green > 10s, yellow 5-10s, red < 5s
            if time_remaining > 10:
                cairo.cairo_set_source_rgb(cr, 0.3, 0.8, 0.3)  # Green
            elif time_remaining > 5:
                cairo.cairo_set_source_rgb(cr, 0.9, 0.7, 0.2)  # Yellow
            else:
                cairo.cairo_set_source_rgb(cr, 0.9, 0.3, 0.3)  # Red
            cairo.cairo_rectangle(cr, 40, bar_y, progress_width, bar_height)
            cairo.cairo_fill(cr)
        
        # Format OTP text with timer
        if self.current_otp:
            otp_text = f"Code 2FA :  {self.current_otp[:3]} {self.current_otp[3:]}  ({time_remaining}s)"
        else:
            otp_text = "Code 2FA :  --- ---"
        
        # Create Pango layout
        layout = pangocairo.pango_cairo_create_layout(cr)
        
        # Set font - Open Sans at specified size (default 20)
        font_desc_str = f"Open Sans {self.font_size}".encode('utf-8')
        font_desc = pango.pango_font_description_from_string(font_desc_str)
        pango.pango_layout_set_font_description(layout, font_desc)
        
        # Set text
        text_bytes = otp_text.encode('utf-8')
        pango.pango_layout_set_text(layout, text_bytes, len(text_bytes))
        
        # Get text size for centering
        text_width = ctypes.c_int()
        text_height = ctypes.c_int()
        pango.pango_layout_get_pixel_size(layout, ctypes.byref(text_width), ctypes.byref(text_height))
        
        # Center text in the full window (horizontally and vertically)
        text_x = (self.width - text_width.value) / 2
        text_y = (self.height - text_height.value) / 2
        
        # Draw text in white (0xFFFFFFFF)
        cairo.cairo_set_source_rgb(cr, 1.0, 1.0, 1.0)
        cairo.cairo_move_to(cr, text_x, text_y)
        pangocairo.pango_cairo_show_layout(cr, layout)
        
        # Cleanup
        cairo.cairo_surface_flush(self.surface)
        pango.pango_font_description_free(font_desc)
        cairo.cairo_destroy(cr)
        
        self.libs['x11'].XFlush(self.display)
    
    def _show_window(self):
        """Show the overlay window and raise it to front."""
        x11 = self.libs['x11']
        if not self.window_visible:
            x11.XMapWindow(self.display, self.window)
            self.window_visible = True
            logger.debug("Overlay window shown")
        # Always raise window to front (in case another app covers it)
        x11.XRaiseWindow(self.display, self.window)
        x11.XFlush(self.display)
    
    def _hide_window(self):
        """Hide the overlay window."""
        if self.window_visible:
            self.libs['x11'].XUnmapWindow(self.display, self.window)
            self.libs['x11'].XFlush(self.display)
            self.window_visible = False
            logger.debug("Overlay window hidden")
    
    def _process_events(self):
        """Process pending X11 events."""
        x11 = self.libs['x11']
        event = XEvent()
        while x11.XPending(self.display) > 0:
            x11.XNextEvent(self.display, ctypes.byref(event))
            if event.type == Expose:
                self._draw()
    
    def update(self):
        """Update OTP display based on auth page activity."""
        auth_active = is_auth_page_active()
        
        if auth_active:
            self._show_window()
            new_otp = read_otp_code()
            if new_otp != self.current_otp:
                self.current_otp = new_otp
                if new_otp:
                    logger.info(f"OTP updated: {new_otp[:3]} {new_otp[3:]}")
            # Always redraw to update countdown timer and progress bar
            self._draw()
        else:
            self._hide_window()
    
    def run(self):
        """Main loop."""
        logger.info("OTP overlay starting...")
        
        # Full initialization with retry - libs, X11, and window creation
        # All of these may fail immediately after boot
        for attempt in range(1, X11_MAX_RETRIES + 1):
            try:
                # Step 1: Load libraries (may fail if system not ready)
                if self.libs is None:
                    if not self._init_libs():
                        raise RuntimeError("Libraries not ready")
                
                # Step 2: Connect to X11
                if not self._init_display():
                    raise RuntimeError("X11 display not ready")
                
                # Step 3: Create window
                if not self._create_window():
                    raise RuntimeError("Window creation failed")
                
                # All good!
                logger.info(f"Initialization successful on attempt {attempt}")
                break
                
            except Exception as e:
                logger.warning(f"Init attempt {attempt}/{X11_MAX_RETRIES} failed: {e}")
                # Cleanup partial state
                if self.display:
                    try:
                        self.libs['x11'].XCloseDisplay(self.display)
                    except:
                        pass
                    self.display = None
                time.sleep(X11_RETRY_DELAY)
        else:
            logger.error(f"Failed to initialize after {X11_MAX_RETRIES} attempts")
            return False
        
        # Clear any stale auth signal from previous run
        clear_auth_signal()
        
        logger.info(f"OTP Cairo overlay started at {self.position}")
        logger.info(f"Font size: {self.font_size}pt")
        logger.info(f"OTP file: {get_otp_file_path()}")
        logger.info(f"Auth signal: {get_auth_signal_path()}")
        
        try:
            while True:
                self._process_events()
                self.update()
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            if self.libs:
                if self.surface:
                    self.libs['cairo'].cairo_surface_destroy(self.surface)
                if self.display:
                    self.libs['x11'].XCloseDisplay(self.display)
        
        return True


def main():
    parser = argparse.ArgumentParser(description='OTP Cairo Overlay')
    parser.add_argument('--position', '-p',
                       choices=['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
                       default='center', help='Overlay position')
    parser.add_argument('--font-size', '-s', type=int, default=32,
                       help='Font size in points (default: 32)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode - show window for 10 seconds')
    
    args = parser.parse_args()
    
    if 'DISPLAY' not in os.environ:
        os.environ['DISPLAY'] = ':0'
    
    overlay = CairoOverlay(position=args.position, font_size=args.font_size)
    
    if args.test:
        if overlay._init_libs() and overlay._init_display() and overlay._create_window():
            overlay.current_otp = "123456"
            overlay._show_window()
            overlay._draw()
            time.sleep(10)
            if overlay.surface:
                overlay.libs['cairo'].cairo_surface_destroy(overlay.surface)
            overlay.libs['x11'].XCloseDisplay(overlay.display)
    else:
        overlay.run()


if __name__ == "__main__":
    main()
