"""Event detail, seat selection, and payment redirection views (TG-184)."""

from datetime import datetime
from typing import Callable, List, Optional

import flet as ft

from mobile_client.components.event_card import _format_event_datetime
from mobile_client.components.navbar import BottomNavBar
from mobile_client.components.seat_matrix import SeatMatrix
from mobile_client.core.constants import EVENT_STATUSES, MAX_TICKETS_PER_EVENT
from mobile_client.core.routes import (
    ROUTE_EVENT_DETAIL,
    ROUTE_EVENTS,
    ROUTE_PAYMENT,
    index_for_route,
)
from mobile_client.core.theme import DEFAULT_THEME, EVENT_STATUS_COLORS
from mobile_client.services.participation_service import (
    ParticipationService,
    ReservationResult,
)


def build_event_detail_view(
    event_id: int = 1,
    participation_service: Optional[ParticipationService] = None,
    on_nav_change: Optional[Callable[[int], None]] = None,
    on_back: Optional[Callable[[], None]] = None,
    on_purchase_success: Optional[Callable[[ReservationResult], None]] = None,
    user_id: Optional[int] = None,
    is_student: bool = False,
    now: Optional[datetime] = None,
    theme=DEFAULT_THEME,
) -> ft.View:
    """Etkinlik detaylarını, koltuk matrisini ve Satın Al / Bekleme Listesi butonlarını gösterir."""
    service = participation_service or ParticipationService()
    detail = service.get_event_detail(event_id, now=now)

    selected_seats: List[str] = []
    feedback_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
    selected_summary_text = ft.Text(
        "Seçili koltuk: Yok",
        size=13,
        color=theme.colors.text_secondary,
    )

    def _safe_update(control: ft.Control) -> None:
        if getattr(control, "page", None) is not None:
            try:
                control.update()
            except Exception:
                pass

    if detail is None:
        return ft.View(
            route=ROUTE_EVENT_DETAIL,
            appbar=ft.AppBar(
                title=ft.Text("Etkinlik Detayı", weight=ft.FontWeight.BOLD),
                bgcolor=theme.colors.background,
            ),
            controls=[
                ft.Container(
                    content=ft.Text(
                        "Etkinlik bulunamadı.",
                        size=14,
                        color=theme.colors.error,
                    ),
                    padding=16,
                )
            ],
            navigation_bar=BottomNavBar(
                selected_index=index_for_route(ROUTE_EVENTS),
                on_change=on_nav_change,
                theme=theme,
            ),
            bgcolor=theme.colors.surface,
        )

    event = detail.event
    status_label = EVENT_STATUSES.get(event.status, event.status.capitalize())
    status_color = EVENT_STATUS_COLORS.get(event.status, theme.colors.text_secondary)
    price_label = "Ücretsiz" if event.price == 0 else f"{int(event.price)} TL"
    formatted_start = _format_event_datetime(event.start_time)
    formatted_end = _format_event_datetime(event.end_time)

    def _handle_seat_selection(codes: List[str]) -> None:
        selected_seats.clear()
        selected_seats.extend(codes)
        if selected_seats:
            selected_summary_text.value = f"Seçili koltuklar: {', '.join(selected_seats)}"
        else:
            selected_summary_text.value = "Seçili koltuk: Yok"
        _safe_update(selected_summary_text)

    seat_matrix = SeatMatrix(
        seats=detail.seats,
        max_selection=MAX_TICKETS_PER_EVENT,
        on_selection_change=_handle_seat_selection,
        theme=theme,
    )

    def _handle_purchase_click(_=None) -> ReservationResult:
        result = service.reserve_seats_for_purchase(
            event_id=event.id,
            seat_codes=list(selected_seats),
            user_id=user_id,
            is_student=is_student,
            now=now,
        )
        feedback_text.value = result.message
        feedback_text.color = theme.colors.success if result.success else theme.colors.error
        _safe_update(feedback_text)
        if result.success and on_purchase_success:
            on_purchase_success(result)
        return result

    def _handle_waitlist_click(_=None) -> bool:
        effective_uid = user_id if user_id is not None else 1
        ok, msg = service.join_waitlist(event.id, user_id=effective_uid, now=now)
        feedback_text.value = msg
        feedback_text.color = theme.colors.success if ok else theme.colors.error
        _safe_update(feedback_text)
        return ok

    purchase_button = ft.ElevatedButton(
        "Satın Al",
        icon=ft.Icons.SHOPPING_CART_CHECKOUT,
        bgcolor=theme.colors.primary,
        color="#FFFFFF",
        disabled=detail.is_sales_closed or detail.is_full or event.status != "published",
        on_click=_handle_purchase_click,
    )

    waitlist_button = ft.OutlinedButton(
        "Bekleme Listesine Katıl",
        icon=ft.Icons.HOURGLASS_TOP,
        visible=detail.is_full and not detail.is_sales_closed,
        on_click=_handle_waitlist_click,
    )

    controls: List[ft.Control] = [
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(
                    event.category,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=theme.colors.primary,
                ),
                ft.Text(
                    status_label,
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=status_color,
                ),
            ],
        ),
        ft.Text(
            event.title,
            size=20,
            weight=ft.FontWeight.BOLD,
            color=theme.colors.text_primary,
        ),
        ft.Text(
            detail.description,
            size=14,
            color=theme.colors.text_secondary,
        ),
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        f"Konum: {detail.venue_name} — {detail.venue_address}",
                        size=13,
                        color=theme.colors.text_primary,
                    ),
                    ft.Text(
                        f"Tarih: {formatted_start} / {formatted_end}",
                        size=13,
                        color=theme.colors.text_primary,
                    ),
                    ft.Text(
                        f"Katılımcı Sayısı: {detail.participant_count} / {event.capacity} "
                        f"(Kalan Kontenjan: {detail.remaining_capacity})",
                        size=13,
                        color=theme.colors.text_primary,
                    ),
                    ft.Text(
                        f"Bilet Fiyatı: {price_label}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=theme.colors.primary,
                    ),
                ],
                spacing=6,
            ),
            padding=12,
            border_radius=8,
            bgcolor=theme.colors.background,
            border=ft.Border.all(1, theme.colors.border),
        ),
    ]

    if detail.sales_status_message:
        controls.append(
            ft.Container(
                content=ft.Text(
                    detail.sales_status_message,
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=theme.colors.error,
                ),
                padding=10,
                border_radius=6,
                bgcolor=theme.colors.background,
                border=ft.Border.all(1, theme.colors.error),
            )
        )

    controls.extend(
        [
            ft.Text(
                f"Koltuk Seçimi (En fazla {MAX_TICKETS_PER_EVENT} koltuk)",
                size=15,
                weight=ft.FontWeight.BOLD,
                color=theme.colors.text_primary,
            ),
            seat_matrix,
            selected_summary_text,
            feedback_text,
            ft.Row(
                controls=[purchase_button, waitlist_button],
                spacing=12,
            ),
        ]
    )

    view = ft.View(
        route=ROUTE_EVENT_DETAIL,
        appbar=ft.AppBar(
            title=ft.Text("Etkinlik Detayı", weight=ft.FontWeight.BOLD),
            bgcolor=theme.colors.background,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: on_back() if on_back else None,
            ),
            automatically_imply_leading=False,
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=controls,
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=16,
                expand=True,
            )
        ],
        navigation_bar=BottomNavBar(
            selected_index=index_for_route(ROUTE_EVENTS),
            on_change=on_nav_change,
            theme=theme,
        ),
        bgcolor=theme.colors.surface,
    )

    view.data = {
        "detail": detail,
        "seat_matrix": seat_matrix,
        "purchase_button": purchase_button,
        "waitlist_button": waitlist_button,
        "feedback_text": feedback_text,
        "selected_seats": selected_seats,
        "trigger_purchase": _handle_purchase_click,
        "trigger_waitlist": _handle_waitlist_click,
    }
    return view


def build_payment_view(
    reservation: Optional[ReservationResult] = None,
    on_nav_change: Optional[Callable[[int], None]] = None,
    on_back: Optional[Callable[[], None]] = None,
    theme=DEFAULT_THEME,
) -> ft.View:
    """Satın Al butonu sonrası yönlendirilen ödeme ekranı görünümü (TG-184)."""
    seats_text = (
        ", ".join(reservation.reserved_seats) if reservation and reservation.reserved_seats else "-"
    )
    total_text = (
        "Ücretsiz"
        if reservation and reservation.total_price == 0
        else f"{reservation.total_price:.2f} TL"
        if reservation
        else "0.00 TL"
    )

    view = ft.View(
        route=ROUTE_PAYMENT,
        appbar=ft.AppBar(
            title=ft.Text("Ödeme", weight=ft.FontWeight.BOLD),
            bgcolor=theme.colors.background,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: on_back() if on_back else None,
            ),
            automatically_imply_leading=False,
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Ödeme Özeti",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=theme.colors.text_primary,
                        ),
                        ft.Text(
                            f"Ayrılan Koltuklar: {seats_text}",
                            size=14,
                            color=theme.colors.text_primary,
                        ),
                        ft.Text(
                            f"Toplam Tutar: {total_text}",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=theme.colors.primary,
                        ),
                    ],
                    spacing=10,
                ),
                padding=16,
            )
        ],
        navigation_bar=BottomNavBar(
            selected_index=index_for_route(ROUTE_EVENTS),
            on_change=on_nav_change,
            theme=theme,
        ),
        bgcolor=theme.colors.surface,
    )
    view.data = {"reservation": reservation}
    return view
