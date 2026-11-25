"""EventHub mobile client application entrypoint and navigation router (TG-160)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.routes import (
    DEFAULT_ROUTE,
    ROUTE_PROFILE,
    ROUTE_TICKETS,
    normalize_route,
    route_for_index,
)
from mobile_client.core.theme import DEFAULT_THEME
from mobile_client.views import (
    build_events_view,
    build_profile_view,
    build_tickets_view,
)


def build_view_for_route(
    route: str,
    on_nav_change: Optional[Callable[[int], None]] = None,
) -> ft.View:
    """Verilen rotaya karşılık gelen boş sayfa görünümünü oluşturur."""
    normalized = normalize_route(route)
    if normalized == ROUTE_TICKETS:
        return build_tickets_view(on_nav_change=on_nav_change)
    if normalized == ROUTE_PROFILE:
        return build_profile_view(on_nav_change=on_nav_change)
    return build_events_view(on_nav_change=on_nav_change)


def main(page: ft.Page) -> None:
    """Uygulama başlangıcı ve temel ekranlar arası gezinme kurulumu."""
    page.title = DEFAULT_THEME.name
    page.bgcolor = DEFAULT_THEME.colors.surface

    def render_route(route: str) -> None:
        normalized = normalize_route(route)
        page.route = normalized
        page.views.clear()
        page.views.append(build_view_for_route(normalized, on_nav_change=handle_nav_change))
        page.update()

    def handle_nav_change(index: int) -> None:
        target_route = route_for_index(index)
        render_route(target_route)

    def handle_route_change(_: Optional[ft.RouteChangeEvent] = None) -> None:
        render_route(page.route or DEFAULT_ROUTE)

    def handle_view_pop(_: Optional[ft.ViewPopEvent] = None) -> None:
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            render_route(top_view.route or DEFAULT_ROUTE)
        else:
            render_route(DEFAULT_ROUTE)

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop

    render_route(page.route or DEFAULT_ROUTE)


if __name__ == "__main__":
    ft.run(main)
