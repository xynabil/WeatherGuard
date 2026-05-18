from domain.models import User, WeatherThreshold


def test_frost_threshold_exceeded(sample_threshold):
    result = sample_threshold.is_exceeded(1.5)

    assert result is True


def test_frost_threshold_not_exceeded():
    threshold = WeatherThreshold(parameter="TTT_C", operator="<", value=5.0, label="Frost", severity="critical")
    result = threshold.is_exceeded(8.0)

    assert result is False


def test_wind_threshold_exceeded():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(72.0)

    assert result is True


def test_wind_threshold_not_exceeded():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(45.0)

    assert result is False


def test_correct_password_accepted():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("admin123")

    assert result is True


def test_wrong_password_rejected():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("falsch")

    assert result is False
