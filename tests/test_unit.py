from domain.models import User, WeatherThreshold


# Test 1: Temperatur 1.5°C liegt unter dem Grenzwert 5°C → Alarm ausgelöst
def test_threshold_exceeded_greater(sample_threshold):
    result = sample_threshold.is_exceeded(1.5)

    assert result is True


# Test 2: Temperatur 8°C liegt über dem Grenzwert 5°C → kein Alarm
def test_threshold_not_exceeded_greater():
    threshold = WeatherThreshold(parameter="TTT_C", operator="<", value=5.0, label="Frost", severity="critical")
    result = threshold.is_exceeded(8.0)

    assert result is False


# Test 3: Wind 72 km/h überschreitet den Grenzwert 60 km/h → Alarm ausgelöst
def test_threshold_exceeded_wind():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(72.0)

    assert result is True


# Test 4: Wind 45 km/h liegt unter dem Grenzwert 60 km/h → kein Alarm
def test_threshold_not_exceeded_wind():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(45.0)

    assert result is False


# Test 5: Richtiges Passwort → Anmeldung erfolgreich
def test_check_password_correct():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("admin123")

    assert result is True


# Test 6: Falsches Passwort → Anmeldung abgelehnt
def test_check_password_wrong():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("falsch")

    assert result is False
