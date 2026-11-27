"""Login and Register views for EventHub mobile client."""

from typing import Callable, Optional

import flet as ft

from mobile_client.core.constants import REGISTER_ROLES
from mobile_client.core.routes import ROUTE_LOGIN, ROUTE_REGISTER
from mobile_client.core.theme import DEFAULT_THEME
from mobile_client.services.auth_service import AuthResult, AuthService


def show_toast(
    page: Optional[ft.Page],
    message: str,
    is_error: bool = False,
) -> None:
    """Kullanıcıya SnackBar (Toast) uyarısı gösterir."""
    if page is None or not hasattr(page, "show_dialog"):
        return
    bgcolor = DEFAULT_THEME.colors.error if is_error else DEFAULT_THEME.colors.success
    snack = ft.SnackBar(
        content=ft.Text(message, color=DEFAULT_THEME.colors.background),
        bgcolor=bgcolor,
        show_close_icon=True,
    )
    try:
        page.show_dialog(snack)
    except Exception:
        pass


def _build_alert_banner() -> tuple[ft.Container, ft.Text]:
    """Form üstünde gösterilecek satır içi uyarı (Alert) kutusunu oluşturur."""
    text_control = ft.Text(
        "",
        size=13,
        color=DEFAULT_THEME.colors.error,
        weight=ft.FontWeight.W_500,
        expand=True,
    )
    banner = ft.Container(
        visible=False,
        bgcolor="#FEF2F2",
        border=ft.Border.all(1, DEFAULT_THEME.colors.error),
        border_radius=8,
        padding=12,
        content=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE, color=DEFAULT_THEME.colors.error, size=18),
                text_control,
            ],
        ),
    )
    return banner, text_control


def _styled_text_field(
    label: str,
    prefix_icon: ft.IconData,
    hint_text: Optional[str] = None,
    helper: Optional[str] = None,
    password: bool = False,
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT,
    visible: bool = True,
    on_submit: Optional[Callable] = None,
) -> ft.TextField:
    """Tema renkleriyle tutarlı TextField bileşeni oluşturur."""
    return ft.TextField(
        label=label,
        hint_text=hint_text,
        helper=helper,
        password=password,
        can_reveal_password=password,
        keyboard_type=keyboard_type,
        prefix_icon=prefix_icon,
        bgcolor=DEFAULT_THEME.colors.surface,
        border_color=DEFAULT_THEME.colors.border,
        focused_border_color=DEFAULT_THEME.colors.primary,
        border_radius=8,
        visible=visible,
        on_submit=on_submit,
    )


def _resolve_page(event: Optional[ft.ControlEvent], fallback_page: Optional[ft.Page]) -> Optional[ft.Page]:
    if fallback_page is not None:
        return fallback_page
    if event is not None and getattr(event, "control", None) is not None:
        return getattr(event.control, "page", None)
    return None


def build_login_view(
    auth_service: Optional[AuthService] = None,
    on_login_success: Optional[Callable[[AuthResult], None]] = None,
    on_navigate: Optional[Callable[[str], None]] = None,
    page: Optional[ft.Page] = None,
    initial_email: str = "",
) -> ft.View:
    """Giriş Yap (Login) ekranını oluşturur."""
    service = auth_service or AuthService()
    alert_banner, alert_text = _build_alert_banner()

    def handle_login(e: Optional[ft.ControlEvent] = None) -> None:
        active_page = _resolve_page(e, page)
        email_field.error = None
        password_field.error = None
        alert_banner.visible = False

        result = service.login(email_field.value or "", password_field.value or "")

        if not result.success:
            if result.field_errors:
                email_field.error = result.field_errors.get("email")
                password_field.error = result.field_errors.get("password")
            alert_text.value = result.message
            alert_banner.visible = True
            show_toast(active_page, result.message, is_error=True)
            if active_page is not None:
                active_page.update()
            return

        show_toast(active_page, result.message, is_error=False)
        if on_login_success:
            on_login_success(result)

    email_field = _styled_text_field(
        label="E-posta Adresi",
        hint_text="ornek@itu.edu.tr",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    if initial_email:
        email_field.value = initial_email

    password_field = _styled_text_field(
        label="Şifre",
        hint_text="Şifrenizi girin",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
        on_submit=handle_login,
    )

    login_button = ft.FilledButton(
        "Giriş Yap",
        icon=ft.Icons.LOGIN,
        width=360,
        height=46,
        on_click=handle_login,
        style=ft.ButtonStyle(
            color=DEFAULT_THEME.colors.background,
            bgcolor=DEFAULT_THEME.colors.primary,
        ),
    )

    go_register_button = ft.TextButton(
        "Hesabınız yok mu? Kayıt Ol",
        on_click=lambda _: on_navigate(ROUTE_REGISTER) if on_navigate else None,
        style=ft.ButtonStyle(color=DEFAULT_THEME.colors.primary),
    )

    form_card = ft.Container(
        width=380,
        padding=24,
        border_radius=8,
        bgcolor=DEFAULT_THEME.colors.background,
        border=ft.Border.all(1, DEFAULT_THEME.colors.border),
        content=ft.Column(
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.EVENT_AVAILABLE, color=DEFAULT_THEME.colors.primary, size=32),
                        ft.Text(
                            DEFAULT_THEME.name,
                            size=26,
                            weight=ft.FontWeight.BOLD,
                            color=DEFAULT_THEME.colors.text_primary,
                        ),
                    ],
                ),
                ft.Text(
                    "Etkinliklere katılmak için hesabınıza giriş yapın.",
                    size=13,
                    color=DEFAULT_THEME.colors.text_secondary,
                    text_align=ft.TextAlign.CENTER,
                ),
                alert_banner,
                email_field,
                password_field,
                login_button,
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[go_register_button],
                ),
                ft.Text(
                    "Demo: users.json içindeki e-posta ile giriş yapabilirsiniz "
                    "(şifre '1234' hatalı kabul edilir).",
                    size=11,
                    color=DEFAULT_THEME.colors.text_secondary,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
        ),
    )

    return ft.View(
        route=ROUTE_LOGIN,
        bgcolor=DEFAULT_THEME.colors.surface,
        scroll=ft.ScrollMode.AUTO,
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=16,
                alignment=ft.Alignment(0, 0),
                content=form_card,
            )
        ],
    )


def build_register_view(
    auth_service: Optional[AuthService] = None,
    on_register_success: Optional[Callable[[AuthResult], None]] = None,
    on_navigate: Optional[Callable[[str], None]] = None,
    page: Optional[ft.Page] = None,
) -> ft.View:
    """Kayıt Ol (Register) ekranını oluşturur (BR-1.1..BR-1.6)."""
    service = auth_service or AuthService()
    alert_banner, alert_text = _build_alert_banner()

    first_name_field = _styled_text_field(
        label="Ad",
        hint_text="Adınız",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )
    last_name_field = _styled_text_field(
        label="Soyad",
        hint_text="Soyadınız",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
    )
    email_field = _styled_text_field(
        label="E-posta Adresi",
        hint_text="ornek@itu.edu.tr",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        keyboard_type=ft.KeyboardType.EMAIL,
    )
    password_field = _styled_text_field(
        label="Şifre",
        helper="8–20 karakter, en az 1 harf ve 1 rakam (BR-1.3)",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
    )
    password_confirm_field = _styled_text_field(
        label="Şifre Tekrar",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        password=True,
    )

    organizer_notice = ft.Container(
        visible=False,
        bgcolor="#EFF6FF",
        border=ft.Border.all(1, DEFAULT_THEME.colors.info),
        border_radius=8,
        padding=10,
        content=ft.Row(
            spacing=8,
            controls=[
                ft.Icon(ft.Icons.INFO_OUTLINE, color=DEFAULT_THEME.colors.info, size=18),
                ft.Text(
                    "Organizatör hesapları yönetici onayından sonra etkinlik oluşturabilir (BR-1.5).",
                    size=12,
                    color=DEFAULT_THEME.colors.secondary,
                    expand=True,
                ),
            ],
        ),
    )

    def handle_role_select(e: ft.ControlEvent) -> None:
        selected_role = role_dropdown.value or "participant"
        organizer_notice.visible = selected_role == "organizer"
        active_page = _resolve_page(e, page)
        if active_page is not None:
            active_page.update()

    role_dropdown = ft.Dropdown(
        label="Hesap Türü",
        value="participant",
        options=[ft.dropdown.Option(key=key, text=label) for key, label in REGISTER_ROLES.items()],
        border_color=DEFAULT_THEME.colors.border,
        focused_border_color=DEFAULT_THEME.colors.primary,
        filled=True,
        fill_color=DEFAULT_THEME.colors.surface,
        on_select=handle_role_select,
    )

    student_number_field = _styled_text_field(
        label="Öğrenci Numarası",
        hint_text="Örn: 2019123456",
        prefix_icon=ft.Icons.BADGE_OUTLINED,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False,
    )

    def handle_student_toggle(e: ft.ControlEvent) -> None:
        is_checked = bool(is_student_checkbox.value)
        student_number_field.visible = is_checked
        if not is_checked:
            student_number_field.value = ""
            student_number_field.error = None
        active_page = _resolve_page(e, page)
        if active_page is not None:
            active_page.update()

    is_student_checkbox = ft.Checkbox(
        label="Üniversite / Yükseköğrenim Öğrencisiyim (BR-1.6)",
        value=False,
        active_color=DEFAULT_THEME.colors.primary,
        on_change=handle_student_toggle,
    )

    notify_email_checkbox = ft.Checkbox(
        label="Etkinlik bildirimlerini e-posta ile almak istiyorum",
        value=True,
        active_color=DEFAULT_THEME.colors.primary,
    )

    terms_checkbox = ft.Checkbox(
        label="Kullanım Koşulları ve Gizlilik Politikası'nı kabul ediyorum",
        value=False,
        active_color=DEFAULT_THEME.colors.primary,
    )

    def open_terms_dialog(e: ft.ControlEvent) -> None:
        active_page = _resolve_page(e, page)
        if active_page is None or not hasattr(active_page, "show_dialog"):
            return
        dialog = ft.AlertDialog(
            title=ft.Text("Kullanım Koşulları ve KVKK"),
            content=ft.Text(
                "EventHub ders projesi kapsamında ad, soyad, e-posta ve isteğe bağlı "
                "öğrenci bilgileriniz yerel JSON deposunda saklanır. Organizatör hesapları "
                "yönetici onayından sonra etkinlik oluşturabilir (BR-1.5).",
                size=13,
                color=DEFAULT_THEME.colors.text_secondary,
            ),
            actions=[
                ft.TextButton("Kapat", on_click=lambda _: active_page.pop_dialog()),
            ],
        )
        active_page.show_dialog(dialog)

    def handle_register(e: Optional[ft.ControlEvent] = None) -> None:
        active_page = _resolve_page(e, page)
        for field in (
            first_name_field,
            last_name_field,
            email_field,
            password_field,
            password_confirm_field,
            student_number_field,
        ):
            field.error = None
        alert_banner.visible = False

        result = service.register(
            first_name=first_name_field.value or "",
            last_name=last_name_field.value or "",
            email=email_field.value or "",
            password=password_field.value or "",
            password_confirm=password_confirm_field.value or "",
            role=role_dropdown.value or "participant",
            is_student=bool(is_student_checkbox.value),
            student_number=student_number_field.value,
            notify_email=bool(notify_email_checkbox.value),
            terms_accepted=bool(terms_checkbox.value),
        )

        if not result.success:
            if result.field_errors:
                first_name_field.error = result.field_errors.get("first_name")
                last_name_field.error = result.field_errors.get("last_name")
                email_field.error = result.field_errors.get("email")
                password_field.error = result.field_errors.get("password")
                password_confirm_field.error = result.field_errors.get("password_confirm")
                student_number_field.error = result.field_errors.get("student_number")
            alert_text.value = result.message
            alert_banner.visible = True
            show_toast(active_page, result.message, is_error=True)
            if active_page is not None:
                active_page.update()
            return

        show_toast(active_page, result.message, is_error=False)
        if on_register_success:
            on_register_success(result)
        elif on_navigate:
            on_navigate(ROUTE_LOGIN)

    register_button = ft.FilledButton(
        "Kayıt Ol",
        icon=ft.Icons.PERSON_ADD,
        width=360,
        height=46,
        on_click=handle_register,
        style=ft.ButtonStyle(
            color=DEFAULT_THEME.colors.background,
            bgcolor=DEFAULT_THEME.colors.primary,
        ),
    )

    go_login_button = ft.TextButton(
        "Zaten hesabınız var mı? Giriş Yap",
        on_click=lambda _: on_navigate(ROUTE_LOGIN) if on_navigate else None,
        style=ft.ButtonStyle(color=DEFAULT_THEME.colors.primary),
    )

    form_card = ft.Container(
        width=380,
        padding=24,
        border_radius=8,
        bgcolor=DEFAULT_THEME.colors.background,
        border=ft.Border.all(1, DEFAULT_THEME.colors.border),
        content=ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                ft.Text(
                    "Hesap Oluştur",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=DEFAULT_THEME.colors.text_primary,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "EventHub'a katılmak için bilgilerinizi doldurun.",
                    size=13,
                    color=DEFAULT_THEME.colors.text_secondary,
                    text_align=ft.TextAlign.CENTER,
                ),
                alert_banner,
                first_name_field,
                last_name_field,
                email_field,
                password_field,
                password_confirm_field,
                role_dropdown,
                organizer_notice,
                ft.Container(
                    bgcolor=DEFAULT_THEME.colors.surface,
                    border=ft.Border.all(1, DEFAULT_THEME.colors.border),
                    border_radius=8,
                    padding=10,
                    content=ft.Column(
                        spacing=8,
                        controls=[is_student_checkbox, student_number_field],
                    ),
                ),
                notify_email_checkbox,
                ft.Row(
                    spacing=4,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Container(content=terms_checkbox, expand=True),
                        ft.TextButton("Oku", on_click=open_terms_dialog),
                    ],
                ),
                register_button,
                ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[go_login_button],
                ),
            ],
        ),
    )

    return ft.View(
        route=ROUTE_REGISTER,
        appbar=ft.AppBar(
            title=ft.Text("Kayıt Ol", weight=ft.FontWeight.BOLD),
            bgcolor=DEFAULT_THEME.colors.background,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=lambda _: on_navigate(ROUTE_LOGIN) if on_navigate else None,
            ),
        ),
        bgcolor=DEFAULT_THEME.colors.surface,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=16,
                alignment=ft.Alignment(0, 0),
                content=form_card,
            )
        ],
    )
