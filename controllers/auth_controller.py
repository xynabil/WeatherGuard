"""AuthController - Login, Registrierung, Passwort ändern."""

from domain.models import User


class AuthController:
    """Kümmert sich um Login und Benutzer-Konten."""

    def __init__(self, user_dao):
        self.user_dao = user_dao

    def verify_login(self, username, password):
        """Prüft Login-Daten. Gibt den User zurück oder None bei falschem Passwort."""
        user = self.user_dao.get_by_username(username)
        if user is not None and user.check_password(password):
            return user
        return None

    def register(self, username, password, confirm_password, company):
        """Registriert einen neuen User.

        Gibt einen Fehlertext zurück (leerer String = alles ok).
        """
        username = username.strip()
        company = company.strip()

        # Einfache Validierung
        if not username or not password:
            return "Bitte Benutzername und Passwort eingeben."
        if len(password) < 6:
            return "Passwort muss mindestens 6 Zeichen haben."
        if password != confirm_password:
            return "Passwörter stimmen nicht überein."
        if self.user_dao.get_by_username(username) is not None:
            return "Benutzername ist bereits vergeben."

        # User in DB anlegen
        new_user = User(username=username, password=password, company=company)
        self.user_dao.add(new_user)
        return ""  # leerer String = erfolgreich

    def change_password(self, username, current_password, new_password):
        """Ändert das Passwort eines Users. Gibt Fehlertext oder "" zurück."""
        if not current_password or not new_password:
            return "Bitte alle Felder ausfüllen."
        if len(new_password) < 6:
            return "Passwort muss mindestens 6 Zeichen haben."

        # Aktuelles Passwort prüfen
        user = self.user_dao.get_by_username(username)
        if user is None or not user.check_password(current_password):
            return "Aktuelles Passwort ist falsch."

        self.user_dao.update_password(username, new_password)
        return ""
