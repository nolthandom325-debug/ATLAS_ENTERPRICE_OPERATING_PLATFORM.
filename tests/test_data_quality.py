from srs.data_validation import validate_all_datasets


def test_validation_function_exists():
    assert callable(validate_all_datasets)


def test_all_datasets_validation_runs():
    validate_all_datasets()