"""Events (home) page with event listing, search, and category filtering (TG-160, TG-183)."""

from typing import Callable, List, Optional

import flet as ft

from mobile_client.components.event_card import EventCard
from mobile_client.components.navbar import BottomNavBar
from mobile_client.core.routes import ROUTE_EVENTS, index_for_route
from mobile_client.core.theme import DEFAULT_THEME
from mobile_client.models.event import Event
from mobile_client.services.event_service import ALL_CATEGORIES_LABEL, EventService

EMPTY_EVENTS_MESSAGE = "Aramanıza uygun etkinlik bulunamadı."


def build_events_view(
    on_nav_change: Optional[Callable[[int], None]] = None,
    event_service: Optional[EventService] = None,
    on_event_click: Optional[Callable[[Event], None]] = None,
    initial_category: str = ALL_CATEGORIES_LABEL,
    initial_search: str = "",
    theme=DEFAULT_THEME,
) -> ft.View:
    """Etkinlikler ana sayfası: arama çubuğu, kategori filtresi ve en yakın tarih sıralı liste."""
    service = event_service or EventService()
    categories = service.get_categories()
    selected_category = initial_category if initial_category in categories else ALL_CATEGORIES_LABEL
    state = {
        "category": selected_category,
        "search": initial_search,
    }

    events_list_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    category_row = ft.Row(spacing=8, scroll=ft.ScrollMode.AUTO)

    def _safe_update(control: ft.Control) -> None:
        try:
            if control.page is not None:
                control.update()
        except (RuntimeError, AttributeError):
            pass

    def _render_events() -> List[Event]:
        filtered_events = service.get_events(
            category=state["category"],
            search_query=state["search"],
        )
        if not filtered_events:
            events_list_column.controls = [
                ft.Container(
                    content=ft.Text(
                        EMPTY_EVENTS_MESSAGE,
                        size=14,
                        color=theme.colors.text_secondary,
                    ),
                    padding=16,
                )
            ]
        else:
            events_list_column.controls = [
                EventCard(event=ev, on_click=on_event_click, theme=theme) for ev in filtered_events
            ]
        _safe_update(events_list_column)
        return filtered_events

    def _select_category(cat: str) -> None:
        state["category"] = cat
        _render_categories()
        _render_events()

    def _render_categories() -> None:
        chips: List[ft.Control] = []
        for cat in categories:
            is_selected = cat == state["category"]
            chips.append(
                ft.Container(
                    content=ft.Text(
                        cat,
                        size=12,
                        weight=ft.FontWeight.BOLD if is_selected else ft.FontWeight.W_500,
                        color="#FFFFFF" if is_selected else theme.colors.text_primary,
                    ),
                    bgcolor=theme.colors.primary if is_selected else theme.colors.background,
                    border=ft.Border.all(
                        1,
                        theme.colors.primary if is_selected else theme.colors.border,
                    ),
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    on_click=lambda _, c=cat: _select_category(c),
                    ink=True,
                )
            )
        category_row.controls = chips
        _safe_update(category_row)

    def _handle_search_change(e: ft.ControlEvent) -> None:
        value = getattr(e, "data", None)
        if value is None and getattr(e, "control", None) is not None:
            value = e.control.value
        state["search"] = str(value or "")
        _render_events()

    search_field = ft.TextField(
        label="Etkinlik Ara",
        hint_text="Başlık, kategori veya tarih ara...",
        value=initial_search,
        prefix_icon=ft.Icons.SEARCH,
        on_change=_handle_search_change,
        border_radius=8,
        bgcolor=theme.colors.background,
    )

    _render_categories()
    _render_events()

    view = ft.View(
        route=ROUTE_EVENTS,
        appbar=ft.AppBar(
            title=ft.Text("Etkinlikler", weight=ft.FontWeight.BOLD),
            bgcolor=theme.colors.background,
            automatically_imply_leading=False,
        ),
        controls=[
            ft.Container(
                content=ft.Column(
                    controls=[
                        search_field,
                        category_row,
                        events_list_column,
                    ],
                    spacing=12,
                ),
                padding=16,
                expand=True,
            ),
        ],
        navigation_bar=BottomNavBar(
            selected_index=index_for_route(ROUTE_EVENTS),
            on_change=on_nav_change,
            theme=theme,
        ),
        bgcolor=theme.colors.surface,
    )

    # Test edilebilirlik için yardımcı referanslar
    view.data = {
        "search_field": search_field,
        "category_row": category_row,
        "events_list_column": events_list_column,
        "select_category": _select_category,
        "set_search": lambda q: (state.__setitem__("search", q), _render_events()),
        "state": state,
    }
    return view
