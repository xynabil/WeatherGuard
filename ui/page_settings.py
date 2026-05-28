"""Seite 5: Settings – Account & Passwort ändern (URL '/settings')."""

from nicegui import ui, app

from ui.components import (
    BG_MAIN, BG_CARD, BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT_BLUE,
    _is_logged_in, _setup_dark_mode, _render_sidebar,
)


def _render_settings_page(auth):
    """Settings-Seite (URL '/settings')."""
    if not _is_logged_in():
        ui.navigate.to("/")
        return

    _setup_dark_mode()
    username = app.storage.user.get("username", "")
    company  = app.storage.user.get("company", "")

    with ui.row().classes("w-full h-screen no-wrap").style("margin: 0; gap: 0;"):
        _render_sidebar("Settings")

        with ui.column().classes("grow").style(
            f"background: {BG_MAIN}; height: 100vh; overflow-y: auto; "
            f"padding: 24px 32px; gap: 24px;"
        ):
            ui.label("Settings").style(
                f"color: {TEXT_PRIMARY}; font-size: 26px; font-weight: 600;"
            )

            # Karte 1: Account-Infos (nur Anzeige, nicht editierbar)
            with ui.column().style(
                f"background: {BG_CARD}; border: 1px solid {BORDER}; "
                f"border-radius: 10px; padding: 24px; gap: 12px; max-width: 480px;"
            ):
                ui.label("Benutzerkonto").style(
                    f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;"
                )
                ui.label(f"Benutzername: {username}").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )
                ui.label(f"Firma: {company or '-'}").style(
                    f"color: {TEXT_MUTED}; font-size: 14px;"
                )

            # Karte 2: Passwort ändern
            _render_change_password_card(auth, username)


def _render_change_password_card(auth, username):
    """Die 'Passwort ändern'-Karte: aktuelles Passwort prüfen, neues setzen."""
    with ui.column().style(
        f"background: {BG_CARD}; border: 1px solid {BORDER}; "
        f"border-radius: 10px; padding: 24px; gap: 16px; max-width: 480px;"
    ):
        ui.label("Passwort ändern").style(
            f"color: {TEXT_PRIMARY}; font-size: 16px; font-weight: 600;"
        )
        current_pw  = ui.input("Aktuelles Passwort", password=True, password_toggle_button=True).classes("w-full")
        new_pw      = ui.input("Neues Passwort",     password=True, password_toggle_button=True).classes("w-full")
        confirm_pw  = ui.input("Passwort bestätigen", password=True, password_toggle_button=True).classes("w-full")
        error_label = ui.label("").style("color: #f47174; font-size: 13px; min-height: 18px;")

        def save_password():
            error_label.set_text("") # Fehlermeldung zurücksetzen
            # Beide neuen Passwörter müssen übereinstimmen
            if new_pw.value != confirm_pw.value:
                error_label.set_text("Neue Passwörter stimmen nicht überein.")
                return
            # Controller prüft das aktuelle Passwort und speichert das neue
            error_message = auth.change_password(username, current_pw.value, new_pw.value)
            if error_message:
                error_label.set_text(error_message)
                return
            # Erfolgreich: Felder leeren
            current_pw.value = ""
            new_pw.value     = ""
            confirm_pw.value = ""
            ui.notify("Passwort erfolgreich geändert!", type="positive")

        ui.button("Speichern", on_click=save_password, icon="save").style(
            f"background: {ACCENT_BLUE}; color: white;"
        )
