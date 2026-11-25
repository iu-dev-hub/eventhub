"""Unit tests for mobile client pages and navigation (TG-160, TG-182)."""

import pytest

from mobile_client.core.routes import (
    DEFAULT_ROUTE,
    NAV_ROUTES,
    ROUTE_EVENTS,
    ROUTE_LOGIN,
    ROUTE_PROFILE,
    ROUTE_REGISTER,
    ROUTE_TICKETS,
    index_for_route,
    is_auth_route,
    normalize_route,
    route_for_index,
)
from mobile_client.models.user import User
from mobile_client.services.auth_service import AuthService


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
        (ROUTE_LOGIN, 0),
        (ROUTE_REGISTER, 0),
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
        ("/login", ROUTE_LOGIN),
        ("/register", ROUTE_REGISTER),
        ("/nonexistent", DEFAULT_ROUTE),
        ("", DEFAULT_ROUTE),
    ],
)
def test_normalize_route(raw_route, expected):
    """Geçerli rotalar korunmalı, bilinmeyen rotalar varsayılan rotaya normalize edilmelidir."""
    assert normalize_route(raw_route) == expected


def test_is_auth_route():
    """Kimlik doğrulama rotaları doğru tanımlanmalıdır."""
    assert is_auth_route(ROUTE_LOGIN) is True
    assert is_auth_route(ROUTE_REGISTER) is True
    assert is_auth_route(ROUTE_EVENTS) is False
    assert is_auth_route(ROUTE_PROFILE) is False


def test_views_and_main_navigation_with_flet():
    """Flet kuruluysa sayfa görünümleri, auth koruması ve ekranlar arası geçiş doğrulanır."""
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

    login_view = build_view_for_route(ROUTE_LOGIN)
    assert login_view.route == ROUTE_LOGIN

    register_view = build_view_for_route(ROUTE_REGISTER)
    assert register_view.route == ROUTE_REGISTER

    class DummyPage:
        def __init__(self):
            self.title = ""
            self.bgcolor = ""
            self.route = "/"
            self.views = []
            self.on_route_change = None
            self.on_view_pop = None
            self.updated = 0
            self.dialogs = []

        def update(self):
            self.updated += 1

        def show_dialog(self, dialog):
            self.dialogs.append(dialog)

    # Giriş yapmamış kullanıcı otomatik olarak Login ekranına yönlendirilmelidir
    unauth_page = DummyPage()
    unauth_service = AuthService()
    main(unauth_page, auth_service=unauth_service)
    assert unauth_page.route == ROUTE_LOGIN
    assert unauth_page.views[0].route == ROUTE_LOGIN

    # Giriş yapmış kullanıcı ana sayfayı ve alt sekmeleri gezebilmelidir
    auth_page = DummyPage()
    auth_service = AuthService()
    auth_service.current_token = "evh_test_token"
    auth_service.current_user = User(
        id=2,
        first_name="Ayşe",
        last_name="Kaya",
        email="ayse.kaya@itu.edu.tr",
        role="participant",
        is_student=True,
        student_number="2019123456",
        notify_email=True,
        avatar_url=None,
        created_at="2024-01-16T10:45:00Z",
        approved=True,
    )
    main(auth_page, auth_service=auth_service)

    assert auth_page.title == "EventHub"
    assert auth_page.route == ROUTE_EVENTS
    assert len(auth_page.views) == 1
    assert auth_page.views[0].route == ROUTE_EVENTS

    # BottomNavBar üzerinden Biletlerim (index=1) sekmesine geçiş
    auth_page.views[0].navigation_bar.nav_callback(1)
    assert auth_page.route == ROUTE_TICKETS
    assert auth_page.views[0].route == ROUTE_TICKETS
    assert auth_page.views[0].navigation_bar.selected_index == 1

    # BottomNavBar üzerinden Profil (index=2) sekmesine geçiş
    auth_page.views[0].navigation_bar.nav_callback(2)
    assert auth_page.route == ROUTE_PROFILE
    assert auth_page.views[0].route == ROUTE_PROFILE
    assert auth_page.views[0].navigation_bar.selected_index == 2

    # BottomNavBar üzerinden tekrar Etkinlikler (index=0) sekmesine geçiş
    auth_page.views[0].navigation_bar.nav_callback(0)
    assert auth_page.route == ROUTE_EVENTS
    assert auth_page.views[0].route == ROUTE_EVENTS
    assert auth_page.views[0].navigation_bar.selected_index == 0
