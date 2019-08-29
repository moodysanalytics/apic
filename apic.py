import sys
import os
import shutil
import logging
import time
import contextlib
from argparse import ArgumentParser
from pyhocon import ConfigFactory
from pyhocon import ConfigMissingException
from types import SimpleNamespace
from datetime import timedelta
from datetime import datetime
from api_client.security import Session
from api_client.security import AuthenticationError
from api_client.file_management_service_client import FileManagementServiceClient
from api_client.dictionary_service_client import DictionaryServiceClient
from api_client.job_service_client import JobServiceClient
from api_client.project_service_client import ProjectServiceClient

LOGIN_ENV_VAR_NAME = 'MA_APIC_LOGIN'
PASSWORD_ENV_VAR_NAME = 'MA_APIC_PASSWORD'

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s\t%(asctime)s\t%(message)s',
    datefmt="%Y-%m-%d %H:%M:%S"
)


def execute_command(current_dir, args):
    """
    Executes ImpairmentStudio command specified in arguments
    :param current_dir: Current, application's directory
    :param args: Parsed command-line arguments for given command
    """
    try:
        # Resolve ImpairmentStudio common option executor
        cmn_opt_executor = resolve_common_option_executor(args)
        if cmn_opt_executor is cmn_opt_exec_version:
            cmn_opt_executor()
            return 0

        # Resolve ImpairmentStudio command executor
        is_cmd_executor = resolve_is_command_executor(args)

        # Get credentials configuration (if any)
        credentials_config = get_credentials_config()

        # Resolve user login and password using sources in the following order:
        # command-line arguments -> environment variables -> credentials configuration
        user_credentials = resolve_user_credentials(args, credentials_config)
        # Validate user credentials if it's not 'configure' command
        if is_cmd_executor is not cmd_exec_configure:
            validate_user_credentials(user_credentials)

        # Get and parse application configuration
        app_config = get_app_config()
        # Validate application configuration
        validate_app_config(app_config)

        if cmn_opt_executor:
            # Run ImpairmentStudio common option executor with provided arguments and user credentials
            cmn_opt_executor(current_dir, args, user_credentials, app_config)
            return 0

        # Run ImpairmentStudio command executor with provided arguments and user credentials
        if is_cmd_executor is cmd_exec_configure:
            is_cmd_executor(user_credentials)
        else:
            is_cmd_executor(current_dir, args, user_credentials, app_config)

        return 0
    except ApicError as e:
        print(e.args[0])
        return 1
    except AuthenticationError as e:
        print(e.args[0])
        return 2
    except KeyboardInterrupt as e:
        print('\nOperation is canceled')
        return 3


def resolve_user_credentials(args, credentials_config):
    user_login = get_credential_item('login', args, LOGIN_ENV_VAR_NAME, 'ma_apic_login', credentials_config)
    user_password = get_credential_item('password', args, PASSWORD_ENV_VAR_NAME, 'ma_apic_password', credentials_config)

    result = SimpleNamespace(
        login=user_login,
        password=user_password
    )

    return result


def validate_user_credentials(user_credentials):
    resolve_message = \
        f"Provide user credentials either in the command line options --login and --password\n" \
        f" or environment variables '{LOGIN_ENV_VAR_NAME}' and '{PASSWORD_ENV_VAR_NAME}'\n" \
        f" or via 'configure' command."
    if not user_credentials:
        raise ApicError(f"User credentials are empty. \n{resolve_message}")

    if not user_credentials.login:
        raise ApicError(f"User login is empty. \n{resolve_message}")

    if not user_credentials.login:
        raise ApicError(f"User password is empty. \n{resolve_message}")


def resolve_common_option_executor(args):
    if args.test_connect:
        return cmn_opt_exec_test_connect
    if args.version:
        return cmn_opt_exec_version

    return None


def resolve_is_command_executor(args):
    is_command_name = get_arg(args, 'is_command_name')
    if not is_command_name:
        return None

    result = is_command_executor_mapping.get(args.is_command_name)
    if not result:
        raise ApicError(f"Unknown ImpairmentStudio™ command '{args.is_command_name}'")

    return result


def get_credentials_config():
    credentials_file_path = get_credentials_file_path()
    if not credentials_file_path:
        return None
    result = ConfigFactory.parse_file(credentials_file_path)
    return result


def get_credentials_file_path():
    credentials_config_dir = os.path.join('~', '.ma')
    credentials_config_dir = os.path.expanduser(credentials_config_dir)
    if not os.path.isdir(credentials_config_dir):
        os.makedirs(credentials_config_dir, exist_ok=True)

    result = os.path.join(credentials_config_dir, 'apic')
    if not os.path.isfile(result):
        with open(result, "a+"):
            pass

    return result


def get_app_config():
    app_config_file_path = get_app_config_file_path()
    if not app_config_file_path:
        return None
    result = ConfigFactory.parse_file(app_config_file_path)
    return result


def validate_app_config(app_config):
    app_config_dir = get_app_config_dir()
    app_config_file_path = get_app_config_file_path()
    resolve_message = \
        f"Configuration file '{app_config_file_path}' either does not exist or corrupt. " \
        f"Delete all *.conf files in the folder '{app_config_dir}' and restart the application."

    if not app_config:
        raise ApicError(f"Configuration is empty. {resolve_message}")


def get_app_config_file_path():
    app_config_dir = get_app_config_dir()
    default_config_dir = 'default_configuration'

    result = affirm_config_file('application.conf', app_config_dir, default_config_dir)

    global_env = os.environ.get('GLOBAL_ENV')
    if global_env and global_env == 'local_dev':
        affirm_config_file('dev_data.conf', app_config_dir, default_config_dir, 'env_data.conf')
    else:
        affirm_config_file('prd_data.conf', app_config_dir, default_config_dir, 'env_data.conf')

    return result


def get_app_config_dir():
    result = os.path.join('~', '.ma')
    result = os.path.expanduser(result)
    if not os.path.isdir(result):
        os.makedirs(result, exist_ok=True)
    return result


def affirm_config_file(file_name, app_config_dir, default_config_dir, destination_file_name=None):
    if not destination_file_name:
        destination_file_name = file_name

    result = os.path.join(app_config_dir, destination_file_name)

    if not os.path.isfile(result):
        default_file_path = os.path.join(default_config_dir, file_name)
        shutil.copy(default_file_path, result)

    return result


def get_credential_item(item_name, args, env_var_name, credentials_config_item_name, credentials_config):
    # Try to get credential item from parsed command-line arguments
    result = get_credential_item_from_args(item_name, args)
    if result:
        return result

    # Try to get credential item from provided environment variable
    result = get_credential_item_from_env_var(env_var_name)
    if result:
        return result

    # Try to get credential item from credentials configuration
    result = get_credential_item_from_credentials_config(credentials_config_item_name, credentials_config)
    if result:
        return result

    # There is no more supported sources of configuration
    return None


def get_credential_item_from_args(item_name, args):
    result = args.__dict__.get(item_name)
    return result


def get_credential_item_from_env_var(env_var_name):
    result = os.environ.get(env_var_name)
    return result


def get_credential_item_from_credentials_config(item_name, credentials_config):
    if not credentials_config:
        return None

    result = get_config_item(credentials_config, item_name)
    return result


def get_item_from_args(item_name, args):
    result = args.__dict__.get(item_name)
    return result


def cmd_exec_import(current_dir, args, user_credentials, app_config):
    # Get/resolve arguments
    arg_input_zip_file_path = args.input_zip
    arg_overwrite = get_arg(args, 'overwrite', default=False)
    arg_job_name = get_arg(args, 'job_name', default='FileUpload')
    arg_error_files_dir = get_arg(args, 'output_path', default=current_dir)

    # Get configuration parameters
    sso_service_base_url = app_config['sso_service_base_url']
    data_api_base_url = app_config['data_api_base_url']
    impairment_studio_api_base_url = app_config['impairment_studio_api_base_url']
    default_job_wait_timeout = timedelta(minutes=app_config['default_job_wait_timeout_in_minutes'])
    proxies = get_requests_proxies(app_config)

    # Run file import in the scope of the authentication session
    with Session(user_credentials.login, user_credentials.password, sso_service_base_url, proxies) as session:
        fms_client = FileManagementServiceClient(session, data_api_base_url)
        ds_client = DictionaryServiceClient(session, data_api_base_url)
        js_client = JobServiceClient(session, impairment_studio_api_base_url)

        # Step 1: Upload ZIP file with inputs to the system's raw files location
        logging.info(f"Importing of the input file '{arg_input_zip_file_path}' to the system has started.")
        head, file_management_file_name = os.path.split(arg_input_zip_file_path)
        files_info = fms_client.import_file(arg_input_zip_file_path, file_management_file_name, 'raw')
        logging.info(f"Importing of the input file '{arg_input_zip_file_path}' to the system has finished.")

        # Step 2.1: Schedule a job to move files from raw files location to processing location
        file_info = files_info[0]
        job_id = ds_client.import_file(
            file_management_file_id=file_info['id'],
            job_name=arg_job_name,
            overwrite=arg_overwrite)
        logging.info(
            f"Moving input file '{file_info['filename']}' from raw files location "
            f"to the processing location has started (job id: '{job_id}').")

        # Step 2.2: Wait until file moving is done
        job_final_status = job_wait(js_client, job_id, default_job_wait_timeout)
        # Step 2.3: Validate job status. If job failed, stop processing and log error.
        validate_job(job_id, job_final_status, fms_client, arg_error_files_dir)
        logging.info(
            f"Moving input file '{file_info['filename']}' from raw files location "
            f"to the processing location has finished (job id: '{job_id}').")


def cmd_exec_analysis(current_dir, args, user_credentials, app_config):
    # Get/resolve arguments
    arg_analysis_id = args.analysis_id
    arg_error_files_dir = get_arg(args, 'output_path', default=current_dir)
    arg_no_wait = get_arg(args, 'no_wait', default=False)

    # Get configuration parameters
    sso_service_base_url = app_config['sso_service_base_url']
    data_api_base_url = app_config['data_api_base_url']
    impairment_studio_api_base_url = app_config['impairment_studio_api_base_url']
    default_job_wait_timeout = timedelta(minutes=app_config['default_job_wait_timeout_in_minutes'])
    proxies = get_requests_proxies(app_config)

    # Run analysis in the scope of the authentication session
    with Session(user_credentials.login, user_credentials.password, sso_service_base_url, proxies) as session:
        ps_client = ProjectServiceClient(session, impairment_studio_api_base_url)
        js_client = JobServiceClient(session, impairment_studio_api_base_url)
        fms_client = FileManagementServiceClient(session, data_api_base_url)

        # Step 3.1: Schedule calculation job
        analysis_job_id = ps_client.run_analysis(arg_analysis_id)
        logging.info(f"Analysis calculation (job id: '{analysis_job_id}') has started.")

        if arg_no_wait:
            return

        # Step 3.2: Wait until calculation is done
        analysis_job_final_status = job_wait(
            js_client,
            analysis_job_id,
            default_job_wait_timeout)
        # Step 3.1: Validate job status. If job failed, stop processing and log error.
        validate_job(analysis_job_id, analysis_job_final_status, fms_client, arg_error_files_dir)
        logging.info(f"Analysis calculation (job id: '{analysis_job_id}') has finished. ")


def cmd_exec_download_results(current_dir, args, user_credentials, app_config):
    # Get/resolve arguments
    arg_analysis_id = args.analysis_id
    arg_output_dir = get_arg(args, 'output_path', default=current_dir)

    # Get configuration parameters
    sso_service_base_url = app_config['sso_service_base_url']
    data_api_base_url = app_config['data_api_base_url']
    proxies = get_requests_proxies(app_config)

    # Run download results in the scope of the authentication session
    with Session(user_credentials.login, user_credentials.password, sso_service_base_url, proxies) as session:
        fms_client = FileManagementServiceClient(session, data_api_base_url)

        # Step 4: Download results
        logging.info(f"Downloading analysis results to the folder '{arg_output_dir}' has started.")
        destination_results_file_name = f"analysis_{arg_analysis_id}_results.zip"
        destination_results_file_path = os.path.join(arg_output_dir, destination_results_file_name)
        fms_client.download_analysis_result_file(arg_analysis_id, destination_results_file_path)
        logging.info(
            f"Downloading analysis results to the file '{destination_results_file_path}' "
            f"in the folder '{arg_output_dir}' has finished.")
        logging.info(f"Analysis run (analysis id: '{arg_analysis_id}') has finished.")


def cmd_exec_configure(user_credentials):
    save_to_file_flag = False
    if user_credentials.login:
        login_prompt_label = f"User login [**********{user_credentials.login[-5:]}]: "
    else:
        login_prompt_label = f"User login: "

    login_prompt_text = input(login_prompt_label)
    if login_prompt_text:
        user_credentials.login = login_prompt_text
        save_to_file_flag = True

    if user_credentials.password:
        password_prompt_label = f"Password [**********{user_credentials.password[-3:]}]: "
    else:
        password_prompt_label = f"Password: "

    password_prompt_text = input(password_prompt_label)
    if password_prompt_text:
        user_credentials.password = password_prompt_text
        save_to_file_flag = True

    if save_to_file_flag:
        update_credentials_file(user_credentials)


def update_credentials_file(user_credentials):
    credentials_file_path = get_credentials_file_path()
    with contextlib.suppress(FileNotFoundError):
        os.remove(credentials_file_path)

    login_text = user_credentials.login if user_credentials.login else 'null'
    password_text = user_credentials.password if user_credentials.password else 'null'

    with open(credentials_file_path, "a+") as credentials_file:
        credentials_file.write(f'ma_apic_login="{login_text}"\n')
        credentials_file.write(f'ma_apic_password="{password_text}"\n')


def cmn_opt_exec_test_connect(current_dir, args, user_credentials, app_config):
    logging.info(f"Connectivity to the services test has started")
    # Get configuration parameters
    sso_service_base_url = app_config['sso_service_base_url']
    data_api_base_url = app_config['data_api_base_url']
    impairment_studio_api_base_url = app_config['impairment_studio_api_base_url']
    default_job_wait_timeout = timedelta(minutes=app_config['default_job_wait_timeout_in_minutes'])
    proxies = get_requests_proxies(app_config)

    # Run connectivity test in the scope of the authentication session
    test_result = True
    with Session(user_credentials.login, user_credentials.password, sso_service_base_url, proxies) as session:
        test_result = session.ping() and test_result

        fms_client = FileManagementServiceClient(session, data_api_base_url)
        ds_client = DictionaryServiceClient(session, data_api_base_url)
        ps_client = ProjectServiceClient(session, impairment_studio_api_base_url)
        js_client = JobServiceClient(session, impairment_studio_api_base_url)

        test_result = fms_client.ping() and test_result
        test_result = ds_client.ping() and test_result
        test_result = ps_client.ping() and test_result
        test_result = js_client.ping() and test_result

        if test_result:
            logging.info('Connectivity to the services test - PASSED')
        else:
            logging.error('Connectivity to the services test - FAILED')


def cmn_opt_exec_version():
    print('API client version 1.0')


def get_requests_proxies(app_config):
    result = {}

    append_requests_proxy_form_config(result, 'http', app_config, 'http_proxy')
    append_requests_proxy_form_config(result, 'https', app_config, 'https_proxy')

    return result


def append_requests_proxy_form_config(proxies, proxy_name, config, config_item_name):
    proxy = get_config_item(config, config_item_name)
    if proxy is not None:
        proxies[proxy_name] = proxy


def get_arg(args, item_name, default=None):
    result = args.__dict__.get(item_name)

    if result:
        return result

    return default


def get_config_item(config, item_name):
    try:
        return config[item_name]
    except ConfigMissingException:
        return None


def job_wait(js_client,  job_id, wait_timeout: timedelta):
    """
    Waits until job is complete successfully or with failures.
    :param js_client: Job service client
    :param job_id: Job id
    :param wait_timeout: Wait time on the client side in seconds.
    :return: Job final status
    """
    wait_begin_datetime = datetime.now()

    while datetime.now() <= wait_begin_datetime + wait_timeout:
        result = js_client.get_job(job_id)
        if result['status'] != 'RUNNING':
            return result
        # Put less load on the job service. Make a delay before the next call
        time.sleep(10)

    raise ApicError(f"Job wait has been terminated by timeout. Job id: {job_id}; timeout: {wait_timeout}.")


def validate_job(job_id, job_final_status, fms_client, error_files_dir):
    """
    Validates job for failed statues and downloads errors to the defined directory
    :param job_id: Job id
    :param job_final_status: The final status of the job to validate
    :param fms_client: File management service client for downloading an error file
    :param error_files_dir: Destination directory for error files on the client side
    """
    if is_job_failed(job_final_status):
        destination_error_file_path = download_error_file(job_id, job_final_status, fms_client, error_files_dir)
        destination_error_file_abs_path = os.path.abspath(destination_error_file_path)
        raise ApicError(
            f"The job 'job type: {job_final_status['type']}; job id: {job_id}' "
            f"stopped by error with status '{job_final_status['status']}'. "
            f"The errors are in the file '{destination_error_file_abs_path}'.")


def is_job_failed(job_status):
    """
    Check job status on failure
    :param job_status: Job status to verify
    :return: True - job has failed; False - job has finished successfully
    """
    job_failed_statuses = ['FAILED', 'COMPLETED_WITH_ERRORS']
    if job_status['status'] in job_failed_statuses:
        return True
    return False


def download_error_file(job_id, job_final_status, fms_client, error_files_dir):
    """
    Downloads error file for the failed jobs or jobs with calculation errors
    :param job_id: Job id
    :param job_final_status: The final status of the job
    :param fms_client: File management service client for downloading an error file
    :param error_files_dir: Destination directory for error files on the client side
    :return: Destination error file path (full name of the file)
    """
    destination_error_file_name = f"job_{job_final_status['type']}_{job_id}_errors.zip"
    destination_error_file_path = os.path.join(error_files_dir, destination_error_file_name)
    fms_client.download_job_import_error_file(job_id, destination_error_file_path)

    return destination_error_file_path


# ImpairmentStudio™ command to executor mapping
is_command_executor_mapping = {
    'import': cmd_exec_import,
    'run-analysis': cmd_exec_analysis,
    'download-results': cmd_exec_download_results,
    'configure': cmd_exec_configure,
}


def add_global_options_to_arg_parser(arguments_parser):
    arguments_parser.add_argument(
        '--login',
        metavar='<user login>',
        help='Specifies the user login to overwrite the environment variable and configuration file')
    arguments_parser.add_argument(
        '--password',
        metavar='<user password>',
        help='Specifies the user password to overwrite the environment variable and configuration file')
    # arguments_parser.add_argument(
    #     '--debug',
    #     action='store_true',
    #     help='A switch that enables debug logging')


# Define top-level command arguments parser and options
arg_parser = ArgumentParser('apic')
arg_parser.add_argument(
    '--test-connect',
    action='store_true',
    default=False,
    help='Test connections to the API servers. Test will be performed on APIs that support ping endpoint')
arg_parser.add_argument(
    '--version',
    action='store_true',
    default=False,
    help="Displays the version of CLI that's currently used")

add_global_options_to_arg_parser(arg_parser)

# Define ImpairmentStudio™ commands and their options
commands_subparser = arg_parser.add_subparsers(help='ImpairmentStudio™ commands')
# 'import' command's argument parser
import_cmd_parser = commands_subparser.add_parser(
    'import',
    help='Imports a zip file containing the data files for ImpairmentStudio™ input')
import_cmd_parser.set_defaults(is_command_name='import')

import_cmd_parser.add_argument(
    '--input-zip',
    required=True,
    metavar='<path to source zip import file>',
    help='The local path to the where output files will be copied to')

import_cmd_parser.add_argument(
    '--output-path',
    metavar='<path to place output files>',
    help='path to place output files')

import_cmd_parser.add_argument(
    '--job-name',
    metavar='<import job name>',
    help='The name of the job to help it get identified in the application')

import_cmd_parser.add_argument(
    '--overwrite',
    action='store_true',
    default=False,
    help='Specifies whether to overwrite portfolio of the same name or not')

add_global_options_to_arg_parser(import_cmd_parser)

# 'run-analysis' command's argument parser
run_analysis_cmd_parser = commands_subparser.add_parser(
    'run-analysis',
    help='Runs an ImpairmentStudio™ analysis')
run_analysis_cmd_parser.set_defaults(is_command_name='run-analysis')

run_analysis_cmd_parser.add_argument(
    '--analysis-id',
    metavar='<analysis id>',
    required=True,
    help='The unique identifier of an analysis that is in ImpairmentStudio™')

run_analysis_cmd_parser.add_argument(
    '--output-path',
    metavar='<path to place output files>',
    help='The local path to the where output files will be downloaded to '
         'after analysis is completed either with error or successfully')

run_analysis_cmd_parser.add_argument(
    '--no-wait',
    action='store_true',
    default=False,
    help='Do not wait for job completion')

add_global_options_to_arg_parser(run_analysis_cmd_parser)

# 'download-results' command's argument parser
download_results_cmd_parser = commands_subparser.add_parser(
    'download-results',
    help='Downloads the output of an analysis that has been executed')
download_results_cmd_parser.set_defaults(is_command_name='download-results')

download_results_cmd_parser.add_argument(
    '--analysis-id',
    metavar='<analysis id>',
    required=True,
    help='The unique identifier of an analysis that is in ImpairmentStudio™')

download_results_cmd_parser.add_argument(
    '--output-path',
    metavar='<path to place output files>',
    help='The local path to the where output files will be downloaded to '
         'after analysis is completed either with error or successfully')

add_global_options_to_arg_parser(download_results_cmd_parser)

# 'configure' command's argument parser
configure_cmd_parser = commands_subparser.add_parser(
    'configure',
    help="Prompts for user credentials in saves to user's credential file")
configure_cmd_parser.set_defaults(is_command_name='configure')


class ApicError(Exception):
    pass


def main():
    app_path = sys.path[0]

    commandline_args = arg_parser.parse_args()
    is_command_name = get_arg(commandline_args, 'is_command_name')
    cmn_opt_test_connect = get_arg(commandline_args, 'test_connect')
    cmn_opt_version = get_arg(commandline_args, 'version')
    if not is_command_name and not cmn_opt_test_connect and not cmn_opt_version:
        arg_parser.print_help()
        exit(1)

    exit_code = execute_command(app_path, commandline_args)
    exit(exit_code)


if __name__ == "__main__":
    main()