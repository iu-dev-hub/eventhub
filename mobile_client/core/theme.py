"""EventHub Mobile Application Theme Configuration.

This file defines the visual themes and styling constants for the mobile application.
"""

from dataclasses import dataclass, field


@dataclass
class ColorPalette:
    """Defines the color scheme for the application."""

    primary: str = "#2563EB"  # Blue-600
    secondary: str = "#1E40AF"  # Blue-700
    success: str = "#10B981"  # Emerald-500
    warning: str = "#F59E0B"  # Amber-500
    error: str = "#EF4444"  # Red-500
    info: str = "#3B82F6"  # Blue-500
    background: str = "#FFFFFF"
    surface: str = "#F9FAFB"
    text_primary: str = "#1F2937"
    text_secondary: str = "#6B7280"
    border: str = "#E5E7EB"


@dataclass
class Typography:
    """Defines typography scales for the application."""

    heading_large: str = "24px"
    heading_medium: str = "20px"
    heading_small: str = "16px"
    body_large: str = "16px"
    body_medium: str = "14px"
    body_small: str = "12px"
    caption: str = "11px"


@dataclass
class Spacing:
    """Defines spacing scale for the application."""

    xs: str = "4px"
    sm: str = "8px"
    md: str = "16px"
    lg: str = "24px"
    xl: str = "32px"


@dataclass
class Theme:
    """Main theme configuration."""

    name: str = "EventHub"
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    border_radius: str = "8px"
    shadow: str = "0 2px 4px rgba(0, 0, 0, 0.1)"


# Default theme instance
DEFAULT_THEME = Theme()

# Event status colors based on business rules
EVENT_STATUS_COLORS = {
    "draft": "#6B7280",  # Gray-500
    "published": "#10B981",  # Emerald-500
    "sales_closed": "#F59E0B",  # Amber-500
    "completed": "#3B82F6",  # Blue-500
    "cancelled": "#EF4444",  # Red-500
}

# Ticket status colors based on business rules
TICKET_STATUS_COLORS = {
    "reserved": "#F59E0B",  # Amber-500
    "paid": "#10B981",  # Emerald-500
    "used": "#3B82F6",  # Blue-500
    "refunded": "#EF4444",  # Red-500
    "cancelled": "#6B7280",  # Gray-500
}

# User role colors
USER_ROLE_COLORS = {
    "participant": "#6B7280",  # Gray-500
    "organizer": "#1E40AF",  # Blue-700
    "admin": "#DC2626",  # Red-600
}
