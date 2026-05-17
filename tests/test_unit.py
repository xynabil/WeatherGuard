from domain.models import User, WeatherThreshold


def test_threshold_exceeded_greater(sample_threshold):
    result = sample_threshold.is_exceeded(1.5)

    assert result is True


def test_threshold_not_exceeded_greater():
    threshold = WeatherThreshold(parameter="TTT_C", operator="<", value=5.0, label="Frost", severity="critical")
    result = threshold.is_exceeded(8.0)

    assert result is False


def test_threshold_exceeded_wind():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(72.0)

    assert result is True


def test_threshold_not_exceeded_wind():
    threshold = WeatherThreshold(parameter="FX_KMH", operator=">", value=60.0, label="Sturm", severity="critical")
    result = threshold.is_exceeded(45.0)

    assert result is False


def test_check_password_correct():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("admin123")

    assert result is True


def test_check_password_wrong():
    user = User(username="admin", password="admin123", company="")
    result = user.check_password("falsch")

    assert result is False
