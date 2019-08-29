# APIC - Moody's Analytics API Command-Line Interface (CLI)
Command-Line Interface (CLI) script to Moody's Analytics API. 
Current version supports API to ImpairmentStudio™.

## Configuring CLI
To configure CLI with what is required to call the APIs, use the **configure** command.
```
$ python apic.pyz configure
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
$ python apic.pyz help
```

The following example displays detailed help for ImpairmentStudio import operation.
```
$ python apic.pyz import help
```

### Common Options
The following command line options can be used to override the configuration settings for a single command:

- **--debug**: A boolean switch that specifies that you want to enable debug logging. An example of this is when CLI is polling for job status, it will print out the current status of the job if debug is turned on.
- **--login**: Specifies the user login to overwrite the environment variable and configuration file.
- **--password**: Specifies the user password to overwrite the environment variable and configuration file.
- **--test-connect**: Test connections to the API servers. Test will be performed on APIs that support ping endpoint.
- **--version**: Displays the version of CLI that's currently used.
