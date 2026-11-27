"""EventHub mobile client application entrypoint and navigation router (TG-160, TG-183, TG-184)."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.constants import (
    TOKEN_STORAGE_KEY,
    USER_EMAIL_STORAGE_KEY,
    USER_ID_STORAGE_KEY,
)
from mobile_client.core.routes import (
    DEFAULT_ROUTE,
    ROUTE_EVENT_DETAIL,
    ROUTE_EVENTS,
    ROUTE_PAYMENT,
    ROUTE_PROFILE,
    ROUTE_REGISTER,
    ROUTE_TICKETS,
    is_auth_route,
    normalize_route,
    route_for_index,
)
from mobile_client.core.theme import DEFAULT_THEME
from mobile_client.models.event import Event
from mobile_client.services.participation_service import (
    ParticipationService,
    ReservationResult,
)
from mobile_client.views import (
    build_event_detail_view,
    build_events_view,
    build_payment_view,
    build_profile_view,
    build_register_view,
    build_tickets_view,
)
from mobile_client.views.auth_view import show_toast


def build_view_for_route(
    route: str,
    on_nav_change: Optional[Callable[[int], None]] = None,
    selected_event_id: int = 1,
    participation_service: Optional[ParticipationService] = None,
    last_reservation: Optional[ReservationResult] = None,
    on_event_click: Optional[Callable[[Event], None]] = None,
    on_purchase_success: Optional[Callable[[ReservationResult], None]] = None,
    on_back: Optional[Callable[[], None]] = None,
) -> ft.View:
    """Verilen rotaya karşılık gelen sayfa görünümünü oluşturur."""
    normalized = normalize_route(route)
    if normalized == ROUTE_LOGIN:
        return build_login_view(
            auth_service=auth_service,
            on_login_success=on_login_success,
            on_navigate=on_navigate,
            page=page,
            initial_email=initial_login_email,
        )
    if normalized == ROUTE_REGISTER:
        return build_register_view(
            auth_service=auth_service,
            on_register_success=on_register_success,
            on_navigate=on_navigate,
            page=page,
        )
    if normalized == ROUTE_TICKETS:
        return build_tickets_view(on_nav_change=on_nav_change)
    if normalized == ROUTE_PROFILE:
        return build_profile_view(on_nav_change=on_nav_change)
    if normalized == ROUTE_EVENT_DETAIL:
        return build_event_detail_view(
            event_id=selected_event_id,
            participation_service=participation_service,
            on_nav_change=on_nav_change,
            on_back=on_back,
            on_purchase_success=on_purchase_success,
        )
    if normalized == ROUTE_PAYMENT:
        return build_payment_view(
            reservation=last_reservation,
            on_nav_change=on_nav_change,
            on_back=on_back,
        )
    return build_events_view(
        on_nav_change=on_nav_change,
        on_event_click=on_event_click,
    )


def main(page: ft.Page, auth_service: Optional[AuthService] = None) -> None:
    """Uygulama başlangıcı, kimlik doğrulama koruması ve ekranlar arası gezinme."""
    page.title = DEFAULT_THEME.name
    page.bgcolor = DEFAULT_THEME.colors.surface
    participation_service = ParticipationService()
    state = {
        "selected_event_id": 1,
        "last_reservation": None,
    }

    def render_route(route: str) -> None:
        normalized = normalize_route(route)
        # Giriş yapmamış kullanıcı korumalı ekranlara erişmeye çalışırsa Login ekranına yönlendir.
        if not is_auth_route(normalized) and not service.is_authenticated:
            normalized = ROUTE_LOGIN
        elif is_auth_route(normalized) and service.is_authenticated:
            normalized = DEFAULT_ROUTE

        page.route = normalized
        page.views.clear()
        page.views.append(
            build_view_for_route(
                normalized,
                on_nav_change=handle_nav_change,
                selected_event_id=state["selected_event_id"],
                participation_service=participation_service,
                last_reservation=state["last_reservation"],
                on_event_click=handle_event_click,
                on_purchase_success=handle_purchase_success,
                on_back=lambda: render_route(ROUTE_EVENTS),
            )
        )
        page.update()

    def handle_event_click(event: Event) -> None:
        state["selected_event_id"] = event.id
        render_route(ROUTE_EVENT_DETAIL)

    def handle_purchase_success(reservation: ReservationResult) -> None:
        state["last_reservation"] = reservation
        render_route(reservation.redirect_route or ROUTE_PAYMENT)

    def handle_nav_change(index: int) -> None:
        target_route = route_for_index(index)
        render_route(target_route)

    def handle_login_success(result: AuthResult) -> None:
        state["prefill_email"] = ""
        _run_background_task(_save_local_token, result)
        render_route(DEFAULT_ROUTE)

    def handle_register_success(result: AuthResult) -> None:
        if result.user:
            state["prefill_email"] = result.user.email
        render_route(ROUTE_LOGIN)

    def handle_logout() -> None:
        service.logout()
        _run_background_task(_clear_local_token)
        show_toast(page, "Oturum kapatıldı.", is_error=False)
        render_route(ROUTE_LOGIN)

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

    if service.is_authenticated:
        render_route(page.route or DEFAULT_ROUTE)
    else:
        render_route(ROUTE_LOGIN)
        _run_background_task(_restore_local_session)


if __name__ == "__main__":
    ft.run(main)
