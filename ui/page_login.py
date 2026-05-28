"""Seite 1: Login & Registrierung (URL '/')."""

from nicegui import ui, app

from ui.components import (
    BG_CARD, BORDER, ACCENT_BLUE, TEXT_PRIMARY, TEXT_MUTED,
    _is_logged_in, _setup_dark_mode,
)


def _render_login_page(auth):
    """Login- und Registrierungs-Seite (URL '/')."""
    # Bereits eingeloggte User direkt zum Dashboard weiterleiten
    if _is_logged_in():
        ui.navigate.to("/dashboard")
        return

    _setup_dark_mode()

    # Karte zentriert auf dem Bildschirm
    with ui.column().classes("absolute-center items-center").style("gap: 0;"):
        # Logo
        with ui.row().classes("items-center no-wrap").style("margin-bottom: 32px; gap: 0;"):
            ui.label("Weather").style(f"color: {TEXT_PRIMARY}; font-size: 28px; font-weight: 700;")
            ui.label("Guard").style(f"color: {ACCENT_BLUE}; font-size: 28px; font-weight: 700;")

        # Karte mit zwei Tabs: Anmelden und Registrieren
        with ui.column().style(
            f"background: {BG_CARD}; border: 1px solid {BORDER}; "
            f"border-radius: 12px; padding: 32px 36px; gap: 16px; width: 340px;"
        ):
            with ui.tabs().classes("w-full").props(f"active-color={ACCENT_BLUE}") as tabs:
                login_tab    = ui.tab("Anmelden")
                register_tab = ui.tab("Registrieren")

            with ui.tab_panels(tabs, value=login_tab).classes("w-full").style(f"background: {BG_CARD};"):
                with ui.tab_panel(login_tab).style("padding: 16px 0 0 0;"):
                    _render_login_form(auth)
                with ui.tab_panel(register_tab).style("padding: 16px 0 0 0;"):
                    _render_register_form(auth)


def _render_login_form(auth):
    """Das eigentliche Login-Formular (innerhalb des 'Anmelden'-Tabs)."""
    username_input = ui.input("Benutzername").classes("w-full")
    password_input = ui.input("Passwort", password=True, password_toggle_button=True).classes("w-full")
    error_label    = ui.label("").style("color: #f47174; font-size: 13px; min-height: 20px;")

    def try_login():
        # Controller prüft Benutzername und Passwort
        user = auth.verify_login(username_input.value, password_input.value)
        if user is None:
            error_label.set_text("Benutzername oder Passwort falsch.")
            return
        # Login erfolgreich: Daten in die Session schreiben
        app.storage.user["logged_in"] = True
        app.storage.user["user_id"]   = user.id #app.storage.user speichert die Session-Daten des eingeloggten Users, damit sie in anderen Seiten abgerufen werden können (z.B. um die Standorte dieses Users zu laden)
        app.storage.user["username"]  = user.username
        app.storage.user["company"]   = user.company
        ui.navigate.to("/dashboard")

    ui.button("Login", on_click=try_login, icon="login").classes("w-full").style(
        f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
    )
    # Hinweis für Demo-Zugang
    ui.label("Demo-Zugang: admin / admin123").style(
        f"color: {TEXT_MUTED}; font-size: 12px; text-align: center; margin-top: 4px;"
    )


def _render_register_form(auth):
    """Registrierungs-Formular (innerhalb des 'Registrieren'-Tabs)."""
    username_input = ui.input("Benutzername *").classes("w-full")
    company_input  = ui.input("Firma", placeholder="Optional").classes("w-full")
    password_input = ui.input("Passwort *", password=True, password_toggle_button=True).classes("w-full")
    confirm_input  = ui.input("Passwort bestätigen *", password=True, password_toggle_button=True).classes("w-full")
    error_label    = ui.label("").style("color: #f47174; font-size: 13px; min-height: 20px;")

    def try_register():
        error_label.set_text("")
        # Controller validiert und legt den User in der DB an
        error_message = auth.register(
            username_input.value,
            password_input.value,
            confirm_input.value,
            company_input.value,
        )
        if error_message:
            error_label.set_text(error_message)
            return
        ui.notify("Konto erstellt! Bitte einloggen.", type="positive")
        ui.navigate.to("/")

    ui.button("Konto erstellen", on_click=try_register, icon="person_add").classes("w-full").style(
        f"background: {ACCENT_BLUE}; color: white; margin-top: 4px;"
    )
