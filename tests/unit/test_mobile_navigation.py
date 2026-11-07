"""Unit tests for mobile client pages and navigation (TG-160)."""

import pytest

from mobile_client.core.routes import (
    DEFAULT_ROUTE,
    NAV_ROUTES,
    ROUTE_EVENTS,
    ROUTE_PROFILE,
    ROUTE_TICKETS,
    index_for_route,
    normalize_route,
    route_for_index,
)


def test_nav_routes_order():
    """Sekme sırası Etkinlikler -> Biletlerim -> Profil olmalıdır."""
    assert NAV_ROUTES == (ROUTE_EVENTS, ROUTE_TICKETS, ROUTE_PROFILE)
    assert DEFAULT_ROUTE == ROUTE_EVENTS


@pytest.mark.parametrize(
    ("route", "expected_index"),
    [
        (ROUTE_EVENTS, 0),
        (ROUTE_TICKETS, 1),
        (ROUTE_PROFILE, 2),
        ("/unknown", 0),
        ("", 0),
    ],
)
def test_index_for_route(route, expected_index):
    """Her rota doğru sekme indeksine eşlenmeli; bilinmeyen rota 0 dönmelidir."""
    assert index_for_route(route) == expected_index


@pytest.mark.parametrize(
    ("index", "expected_route"),
    [
        (0, ROUTE_EVENTS),
        (1, ROUTE_TICKETS),
        (2, ROUTE_PROFILE),
        (-1, DEFAULT_ROUTE),
        (3, DEFAULT_ROUTE),
        (99, DEFAULT_ROUTE),
    ],
)
def test_route_for_index_boundary_values(index, expected_route):
    """Geçerli ve sınır dışı sekme indeksleri doğru rotaya eşlenmelidir."""
    assert route_for_index(index) == expected_route


@pytest.mark.parametrize(
    ("raw_route", "expected"),
    [
        ("/", ROUTE_EVENTS),
        ("/tickets", ROUTE_TICKETS),
        ("/profile", ROUTE_PROFILE),
        ("/nonexistent", DEFAULT_ROUTE),
        ("", DEFAULT_ROUTE),
    ],
)
def test_normalize_route(raw_route, expected):
    """Bilinmeyen rotalar varsayılan rotaya normalize edilmelidir."""
    assert normalize_route(raw_route) == expected


def test_views_and_main_navigation_with_flet():
    """Flet kuruluysa boş sayfa görünümleri ve ekranlar arası geçiş doğrulanır."""
    pytest.importorskip("flet")
    from mobile_client.main import build_view_for_route, main

    events_view = build_view_for_route(ROUTE_EVENTS)
    assert events_view.route == ROUTE_EVENTS
    assert events_view.navigation_bar.selected_index == 0

    tickets_view = build_view_for_route(ROUTE_TICKETS)
    assert tickets_view.route == ROUTE_TICKETS
    assert tickets_view.navigation_bar.selected_index == 1

    profile_view = build_view_for_route(ROUTE_PROFILE)
    assert profile_view.route == ROUTE_PROFILE
    assert profile_view.navigation_bar.selected_index == 2

    class DummyPage:
        def __init__(self):
            self.title = ""
            self.bgcolor = ""
            self.route = "/"
            self.views = []
            self.on_route_change = None
            self.on_view_pop = None
            self.updated = 0

        def update(self):
            self.updated += 1

    page = DummyPage()
    main(page)

    assert page.title == "EventHub"
    assert page.route == ROUTE_EVENTS
    assert len(page.views) == 1
    assert page.views[0].route == ROUTE_EVENTS

    # BottomNavBar üzerinden Biletlerim (index=1) sekmesine geçiş
    page.views[0].navigation_bar.nav_callback(1)
    assert page.route == ROUTE_TICKETS
    assert page.views[0].route == ROUTE_TICKETS
    assert page.views[0].navigation_bar.selected_index == 1

    # BottomNavBar üzerinden Profil (index=2) sekmesine geçiş
    page.views[0].navigation_bar.nav_callback(2)
    assert page.route == ROUTE_PROFILE
    assert page.views[0].route == ROUTE_PROFILE
    assert page.views[0].navigation_bar.selected_index == 2

    # BottomNavBar üzerinden tekrar Etkinlikler (index=0) sekmesine geçiş
    page.views[0].navigation_bar.nav_callback(0)
    assert page.route == ROUTE_EVENTS
    assert page.views[0].route == ROUTE_EVENTS
    assert page.views[0].navigation_bar.selected_index == 0
