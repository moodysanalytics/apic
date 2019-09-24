# APIC - Moody's Analytics API Command-Line Interface (CLI)
Command-Line Interface (CLI) script to Moody's Analytics API. 
Current version supports API to ImpairmentStudio™.

## Configuring CLI
To configure CLI with what is required to call the APIs, use the **configure** command.
```
$ python apic configure
User login: USERLOGIN
Password: USERPASSWORD
```

The **configure** command prompts for 3 pieces of information:
- User login: The user name to logs in the system. This is provisioned by MA.
- Password: The password for the user login
This will generate a key value pair file at ```~/.ma/apic``` or ```C:\Users\[USERNAME]\.ma\apic```

```
ma_apic_login = USERLOGIN
ma_apic_password = USERPASSWORD
```

### Configuration Settings and Precedence
The CLI uses a set of _credential providers_ to look for credentials to be used to call the APIs. Each credential provider looks for credentials in a different place, such as the system or user environment variables, local configuration files, or explicitly declared on the command line as a parameter. The CLI looks for credentials and configuration settings by invoking the providers in the following order, stopping when it finds a set of credentials to use:
1.	Command line options: Specifies **--login**, and **--password** as parameter to the command line
2.	Environment variables: **MA_APIC_LOGIN** and **MA_APIC_PASSWORD** can be used to store the user login and password
3.	Configuration file: This is the file that is created/updated when apic configure. The file is located at ```~/.ma/apic on``` Unix, Linux, or MacOS, or ```C:\Users\[USERNAME]\.ma\apic``` on Windows.

### Using HTTP Proxy
To access the APIs through proxy servers, you can configure the **HTTP_PROXY** and **HTTPS_PROXY** environment variables with either the DNS domain names or IP addresses and port numbers used by your proxy servers.

On Unix, Linux, macOS.
```
$ export HTTP_PROXY=http://10.15.20.25:1234
$ export HTTP_PROXY=http://proxy.example.com:1234
$ export HTTPS_PROXY=http://10.15.20.25:5678
$ export HTTPS_PROXY=http://proxy.example.com:5678
```

On Windows.
```
C:\> set HTTP_PROXY http://10.15.20.25:1234
C:\> set HTTP_PROXY=http://proxy.example.com:1234
C:\> set HTTPS_PROXY=http://10.15.20.25:5678
C:\> set HTTPS_PROXY=http://proxy.example.com:5678
```

## Common CLI Commands and Options
### Common Commands

Help is presented with any command when using the CLI. To do so, simply use **help** command at the end of the line.

For example, the following command displays help for the general CLI options and the available top-level commands.
```
The following command displays the available ImpairmentStudio commands.
$ python apic help
```

The following example displays detailed help for ImpairmentStudio™ import operation.
```
$ python apic import help
```

### Common Options
The following command line options can be used to override the configuration settings for a single command:

- **--debug**: A boolean switch that specifies that you want to enable debug logging. An example of this is when CLI is polling for job status, it will print out the current status of the job if debug is turned on.
- **--login**: Specifies the user login to overwrite the environment variable and configuration file.
- **--password**: Specifies the user password to overwrite the environment variable and configuration file.
- **--test-connect**: Test connections to the API servers. Test will be performed on APIs that support ping endpoint.
- **--version**: Displays the version of CLI that's currently used.


## ImpairmentStudio™ CLI Commands
### Import Data
Imports a zip file containing the data files for ImpairmentStudio™ input.

```
python apic import
  --input-zip <path to source zip import file>
  [--output-path <path to place output files>]
  [--job-name <import job name>]
  [--overwrite]
Options
--input-zip (string)
```
The local path to the input zip file to be imported.

Example: ```/my-data/in/portfolio_201908.zip```

```--output-path (string)```

The local path to the where output files will be copied to. The output files for import contains the zip of error messages from the validation process. The name of the zip file will be the same as the name of the input file with _out suffix. If a file with the same name existed, it will be overwritten.



Default value: When not specified, this will default to the same directory as the input file. In the example where the input file is /my-data/in/portfolio_201908.zip, the output file will be placed at /my-data/in/portfolio_201908_out.zip

Example: ```/my-data/out will create file /my-data/out/portfolio_201908_out.zip```

```--job-name (string)```

The name of the job to help it get identified in the application.

Default value When not specified, The job name will be the name of the input zip file without zip file extension. When input file is /my-data/in/portfolio_201908.zip, the job name will be portfolio_201908.

```--overwrite```

Specifies whether to overwrite portfolio of the same name or not.

Default value: When not is specified, and the same portfolio name and as of date existed, error will be returned

### Run Analysis
Runs an ImpairmentStudio™ analysis.

If analysis id does not exist, error message will be returned.

```
python apic run-analysis
  --analysis-id <analysis id>
  [--output-path <<path to place output files>]
  [--no-wait]
Options
  --analysis-id (number)
```
The unique identifier of an analysis that is in ImpairmentStudio™. This identifier can be retrieved from ImpairmentStudio™ application.

```--output-path (string)```

The local path to the where output files will be downloaded to after analysis is completed either with error or successfully. The output file for analysis contains a zip of results and error messages from the analysis process. The name of the zip file will follow the following format: analysis_<analysis-id>_out.zip. If a file with the same name existed, it will be overwritten.

If no output path is specified, then the output file will not be downloaded after analysis is completed.

Example: ```/my-analysis/res for analysis id 256 will create file /my-analysis/res/analysis_256_out.zip```

```--no-wait```

Do not wait for job completion. This results in the call to return immediately after the job is submitted. It will be ignored if --output-path is specified and the command will wait for completion.

Default value: If not specified, wait and monitor for completion.

### Download Analysis Output
Downloads the output of an analysis that has been executed. This downloads the same zip file as when specified in the run-analysis command.

If analysis id does not exist, or the analysis has never been run, error message will be returned.
```
python apic download-analysis-output
  --analysis-id <analysis id>
  [--output-path <<path to place output files>]
Options
  --analysis-id (number)
```
The unique identifier of an analysis that is in ImpairmentStudio™. This identifier can be retrieved from ImpairmentStudio™ application.

```--output-path (string)```

The local path to the where output files will be downloaded to after analysis is completed either with error or successfully. The output file for analysis contains a zip of results and error messages from the analysis process. The name of the zip file will follow the following format: analysis_<analysis-id>_out.zip. If a file with the same name existed, it will be overwritten.

If no output path is specified, then the output file will not be downloaded after analysis is completed.

Example: ```/my-analysis/res for analysis id 256 will create file /my-analysis/res/analysis_256_out.zip```