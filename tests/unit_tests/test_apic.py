import apic
import os
import contextlib
from types import SimpleNamespace
from pyhocon import ConfigFactory


def test_resolve_user_credentials_all_sources_are_empty():
    create_empty_credentials_file()
    credentials_config = apic.get_credentials_config()
    args = SimpleNamespace(
        debug=False,
        test_connect=True)

    actual = apic.resolve_user_credentials(args, credentials_config)

    assert actual.login is None
    assert actual.password is None


def test_get_credential_item_from_args():
    expected = 'user_123'
    args = SimpleNamespace(
        debug=False,
        login=expected,
        password='top_secret',
        test_connect=True)

    actual = apic.get_credential_item_from_args('login', args)
    assert actual == expected
    print_actual(actual)


def test_get_credential_missing_item_from_args():
    args = SimpleNamespace(
        debug=False,
        password='top_secret',
        test_connect=True)

    actual = apic.get_credential_item_from_args('login', args)
    assert actual is None
    print_actual(actual)


def test_get_credential_item_from_env_var():
    env_var_name = 'MA_APIC_PASSWORD_MISSING'
    actual = apic.get_credential_item_from_env_var(env_var_name)
    assert actual is None


def test_get_credential_item_from_missing_env_var():
    env_var_name = 'MA_APIC_LOGIN_FOR_TESTING'
    expected = 'user_xyz'
    os.environ[env_var_name] = expected
    actual = apic.get_credential_item_from_env_var(env_var_name)
    assert actual == expected
    del os.environ[env_var_name]


def test_get_credential_item_from_credentials_config():
    # Prepare initial state
    item_name = 'ma_apic_login'
    item_value = 'user_abc'
    item2_name = 'ma_apic_password'
    item2_value = 'top_secret'
    create_credentials_file(item_name, item_value, item2_name, item2_value)
    credentials_config = apic.get_credentials_config()

    # Run the test
    actual = apic.get_credential_item_from_credentials_config(item_name, credentials_config)
    assert actual == item_value
    print_actual(actual)


def test_get_credential_item_from_empty_credentials_config():
    # Prepare initial state
    create_empty_credentials_file()
    credentials_config = apic.get_credentials_config()

    actual = apic.get_credential_item_from_credentials_config('login', credentials_config)
    assert actual is None


def test_get_missing_credential_item_from_credentials_config():
    # Prepare initial state
    item_name = 'loginErratum'
    item_value = 'user_abc'
    item2_name = 'ma_apic_password'
    item2_value = 'top_secret'
    create_credentials_file(item_name, item_value, item2_name, item2_value)
    credentials_config = apic.get_credentials_config()

    # Run the test
    actual = apic.get_credential_item_from_credentials_config('login', credentials_config)
    assert actual is None
    print_actual(actual)


def test_get_credentials_file_path():
    expected = os.path.expanduser('~\\.ma\\apic')
    with contextlib.suppress(FileNotFoundError):
        os.remove(expected)
    actual = apic.get_credentials_file_path()
    assert actual == expected
    assert os.path.exists(actual)
    print_actual(actual)


def test_get_credentials_config():
    actual = apic.get_credentials_config()
    assert actual is not None
    print_actual(actual)


def test_get_app_config():
    actual = apic.get_app_config()

    assert actual['sso_service_base_url'] == 'https://qa-api.sso.moodysanalytics.net'
    assert actual['data_api_base_url'] == 'https://qa-api.rafa.moodysanalytics.net'
    assert actual['impairment_studio_api_base_url'] == 'https://qa-api.impairmentstudio.moodysanalytics.net'


def test_get_app_config_file_path():
    expected = os.path.expanduser('~\\.ma\\application.conf')
    expected_prd_data_conf_file_path = os.path.expanduser('~\\.ma\\application.conf')

    with contextlib.suppress(FileNotFoundError):
        os.remove(expected)
    with contextlib.suppress(FileNotFoundError):
        os.remove(expected_prd_data_conf_file_path)

    actual = apic.get_app_config_file_path()

    assert actual == expected
    assert os.path.exists(actual)
    assert os.path.exists(expected_prd_data_conf_file_path)

    # And, one more time for existing files
    actual = apic.get_app_config_file_path()
    assert actual == expected
    assert os.path.exists(actual)
    assert os.path.exists(expected_prd_data_conf_file_path)

    print_actual(actual)


def test_get_config_item():
    config = ConfigFactory.parse_file('default_configuration\\application.conf')
    actual = apic.get_config_item(config, 'non_existing_item')
    assert actual is None

    actual = apic.get_config_item(config, 'sso_service_base_url')
    assert actual == 'https://qa-api.sso.moodysanalytics.net'


def test_get_arg():
    args = SimpleNamespace(
        job_name=None
    )

    actual = apic.get_arg(args, 'login')
    assert actual is None
    actual = apic.get_arg(args, 'login', None)
    assert actual is None
    actual = apic.get_arg(args, 'login', default='bankx_user1')
    assert actual == 'bankx_user1'

    actual = apic.get_arg(args, 'job_name')
    assert actual is None
    actual = apic.get_arg(args, 'job_name', None)
    assert actual is None
    actual = apic.get_arg(args, 'job_name', default='FileUpload')
    assert actual == 'FileUpload'
    actual = apic.get_arg(args, 'job_name', 'File_Upload')
    assert actual == 'File_Upload'


def create_credentials_file(item1_name, item1_value, item2_name, item2_value):
    credentials_file_path = apic.get_credentials_file_path()
    with contextlib.suppress(FileNotFoundError):
        os.remove(credentials_file_path)

    with open(credentials_file_path, "a+") as credentials_file:
        credentials_file.write(f"{item1_name}={item1_value}\n")
        credentials_file.write(f"{item2_name}={item2_value}\n")


def create_empty_credentials_file():
    credentials_file_path = os.path.expanduser('~\\.ma\\apic')
    with contextlib.suppress(FileNotFoundError):
        os.remove(credentials_file_path)
    result =  apic.get_credentials_file_path()
    return result


def print_actual(actual):
    print(f"\n---------------------\nActual:\n{actual}")
