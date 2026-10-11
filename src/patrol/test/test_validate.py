from patrol.patrol import validate_param


def test_valid_values():
    assert validate_param('linear_speed', 0.5) is True
    assert validate_param('linear_speed', 0.0) is True
    assert validate_param('linear_speed', 1.0) is True
    assert validate_param('turn_rate', -1.0) is True
    assert validate_param('turn_rate', 1.0) is True
    assert validate_param('publish_hz', 1.0) is True
    assert validate_param('publish_hz', 30.0) is True
    assert validate_param('publish_hz', 5.0) is True


def test_out_of_range():
    assert validate_param('linear_speed', -0.1) is False
    assert validate_param('linear_speed', 1.1) is False
    assert validate_param('turn_rate', -1.1) is False
    assert validate_param('turn_rate', 1.1) is False
    assert validate_param('publish_hz', 0.0) is False
    assert validate_param('publish_hz', 0.9) is False
    assert validate_param('publish_hz', 30.1) is False
    assert validate_param('publish_hz', -5.0) is False


def test_nan_and_inf():
    assert validate_param('publish_hz', float('nan')) is False
    assert validate_param('publish_hz', float('inf')) is False
    assert validate_param('publish_hz', float('-inf')) is False
    assert validate_param('linear_speed', float('nan')) is False
    assert validate_param('turn_rate', float('nan')) is False
