"""Route definitions and navigation mapping for the mobile client (TG-160, TG-184).

Bu modül flet içe aktarmaz; böylece gezinme mantığı CI'da flet kurulmadan
test edilebilir (mobile_client/README.md - test edilebilirlik kuralı).
"""

ROUTE_EVENTS = "/"
ROUTE_TICKETS = "/tickets"
ROUTE_PROFILE = "/profile"
ROUTE_EVENT_DETAIL = "/event-detail"
ROUTE_PAYMENT = "/payment"

# Alt gezinme çubuğundaki sekme sırası (BottomNavBar ile aynı sırada olmalıdır).
NAV_ROUTES = (ROUTE_EVENTS, ROUTE_TICKETS, ROUTE_PROFILE)
DETAIL_FLOW_ROUTES = (ROUTE_EVENT_DETAIL, ROUTE_PAYMENT)
VALID_ROUTES = (*NAV_ROUTES, *DETAIL_FLOW_ROUTES)

DEFAULT_ROUTE = ROUTE_EVENTS


def index_for_route(route: str) -> int:
    """Rotaya karşılık gelen sekme sırasını döndürür; bilinmeyen rota için 0."""
    if route in NAV_ROUTES:
        return NAV_ROUTES.index(route)
    return 0


def route_for_index(index: int) -> str:
    """Sekme sırasına karşılık gelen rotayı döndürür; geçersiz sıra için varsayılan rota."""
    if 0 <= index < len(NAV_ROUTES):
        return NAV_ROUTES[index]
    return DEFAULT_ROUTE


def normalize_route(route: str) -> str:
    """Bilinmeyen veya boş rotaları varsayılan rotaya yönlendirir."""
    if route in VALID_ROUTES:
        return route
    return DEFAULT_ROUTE
