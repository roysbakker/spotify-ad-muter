# Information

Spotify Ad Muter is a program written in Python 3 and is intended for use with the Spotify Free subscription plan. Though ads cannot be avoided if one does not have Spotify Premium, they can at the very least be muted with this program. It makes use of the [Spotify Web API](https://developer.spotify.com/documentation/web-api) to poll the intended device's active song. If it detects an ad being played, Spotify Ad Muter stores the current volume level, sets it to a user-specified level for the duration of the ads, and afterwards restores the original volume level. It is important to note that this program **does not save any user data** and only looks at the duration of the playing song and the type (song, podcast, or ad). No data is sent from the user's device in any way.

The Python program has the following options:

| *Short-form* 	| *Long-form*          	| *Argument*      	| *Info*                                                                                                                              	|
|--------------	|----------------------	|------------------	|--------------------------------------------------------------------------------------------------------------------------------------	|
| `-h`          | `--help`              | -                 | Shows program information and options                                                                                               	|
| `-c`         	| `--auto_close`       	| -               	| Closes this program automatically if Spotify is not an active process on this machine                                               	|
| `-a <arg>`   	| `--ad_volume <arg>`  	| Integer [0-100] 	| Sets the percentage of normal volume at which ads will play (default: 10%)                                                          	|
| `-t <arg>`   	| `--dev_name <arg>`   	| String          	| Sets the target device name on which Spotify is running (default: system host name)                                                 	|
| `-p <arg>`   	| `--cache_path <arg>` 	| File path       	| Sets the file path of the file in which to cache authentication information (default: in OS' documents directory as `.cache`)       	|
| `-l <arg>`   	| `--log_path <arg>`   	| File path       	| Sets the file path of the file in which to store program log information (default: in OS' temp directory as `spotify-ad-muter.log`) 	|

# General Setup

- Create a Spotify web app (see [here](https://developer.spotify.com/documentation/web-api/tutorials/getting-started)).
- Set environment variables for client ID (`SPOTIPY_CLIENT_ID`) and redirect URI (`SPOTIPY_REDIRECT_URI`) as obtained after creating the Spotify web app (see [here](https://spotipy.readthedocs.io/en/2.22.1/#quick-start)).
    - Linux:
        - Use the `export <env-var>=<value>` command to set the aforementioned environment variables.
        - Put these commands in `~/.bash_profile`, `~/.profile`, or similar to set the environment variables persistently for the active user.
    - Windows:
        - Use [this](https://docs.oracle.com/en/database/oracle/machine-learning/oml4r/1.5.1/oread/creating-and-modifying-environment-variables-on-windows.html#GUID-DD6F9982-60D5-48F6-8270-A27EC53807D0) guide.
- Run the Python script locally in a terminal first to check if no errors are reported regarding missing library imports and/or incorrect application configurations.
    - If any Python library is missing, it may be installed using [`pip`](https://packaging.python.org/en/latest/tutorials/installing-packages/).
    - Additional debug information during execution is provided in a log file. Its location can be specified with the `-l` option. If its location is not explicitly specified, the default location is:
        - *Linux*: `/tmp/spotify-ad-muter.log`.
        - *Windows*: `$TEMP\spotify-ad-muter.log` (here `$TEMP` is an environment variable).

# Link to Spotify
To ensure the Spotify Ad Muter program runs when Spotify is active, the following sections describe setups for both Linux and Windows operating systems. For both operating systems, two setups are explained: one where Spotify Ad Muter is started and closed when Spotify itself is started and closed and another which runs the Spotify Ad Muter program indefinitely after system startup. Pros and cons are outlined for each setup.

## Linux

### Setup: start and close the program along with Spotify
This setup uses the `.desktop` file of a the installed Spotify client to start a Spotify Ad Muter instance on startup of the Spotify client itself. Note that this therefore only works when launching Spotify using the OS' graphical user interface and does not work when starting Spotify via a command line interface.

- Find and change the desktop file belonging to the Spotify client installed on the Linux machine (e.g. [Arch Linux' `spotify-launcher`](https://archlinux.org/packages/extra/x86_64/spotify-launcher/))
    - Run `find /usr/ -iregex ".*\.desktop"` to find the location of the client's `.desktop` file (e.g. `/usr/share/applications/spotify-launcher.desktop`)
    - Substitute the existing value for the `Exec` key (i.e. `Exec=<spotify-client>`) for the snippet below
        - Note: the `sleep` command is used to give spotify some time to start up, because otherwise the Spotify Ad Muter program might immediately close if it cannot find a running Spotify process
```.desktop
Exec=/bin/bash -c "<spotify-client> & sleep 5 ; python3 <absolute-dirpath>/spotify_ad_muter.py -c -p <absolute-filepath-to-cache-file>"
```

### Setup: run program from log on until log off
This setup uses [`cron`](https://wiki.archlinux.org/title/Cron) to start the Spotify Ad Muter program at startup. The started instance runs indefinitely until the user powers off.

- Add a cron job that starts the Spotify Ad Muter program at startup
    - Run `crontab -e` to edit the user crontab
    - Add the line below to the crontab file:
        - The `.bash_profile` file (or `.profile` file) is sourced first to import the earlier mentioned required environment variables (these may also be exported explicitly)
        - The `sleep` command is used to give the system time to initialize (e.g. the ALSA system needs to be initialized first)
```cron
@reboot . $HOME/.bash_profile; sleep 10; /bin/python3 <absolute-dirpath>/spotify_ad_muter.py -p <absolute-filepath-to-cache>
```

## Windows

### Setup: start and close the program along with Spotify
This setup uses Windows' built-in audit process tracking capability to provide a trigger when a new Spotify instance is launched. This is used by a custom task to start the Spotify Ad Muter program. The program is run with the `--auto_close` flag such that it is automatically closed when Spotify is closed.

- If MS Windows 10 Home is used, run the following two commands in the command prompt (as administrator) to enable the Group Policy Editor `gpedit.msc`:
    - `FOR %F IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientTools-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%F")`
    - `FOR %F IN ("%SystemRoot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientExtensions-Package~*.mum") DO (DISM /Online /NoRestart /Add-Package:"%F")`
- Change the audit process tracking policy to enable tracking of, among other things, 'successful' process creations:
    - Run `gpedit.msc` and navigate to *Computer Configuration -> Windows Settings -> Security Settings -> Local Policies -> Audit Policy*
    - Open *Audit process tracking* properties and enable 'success' events
    - Run `gpupdate /force` in a command prompt (as administrator) to apply the previous changes
- Create a Visual Basic Script (VBS) file, which is used to indirectly call the Python script:
```VBS
Set WshShell = CreateObject("WScript.Shell")
Call WshShell.Run("python3 <absolute-dirpath>\spotify_ad_muter.py -c -p <absolute-filepath-to-cache-file>", 0)
Set WshShell = Nothing
```
- Create a task that runs the VBS file when Spotify is started:
	- Run `taskschd.msc` and navigate to *Action -> Create Task...*
	- Provide the task name (e.g. "spotify-ad-muter-starter") and optionally a description 
	- Set it to run only when the current user is logged on
	- Go to the *Actions* tab and click *New...*
	- Set *Action* to "Start a program"
	- Link to the previously created VBS file
	- Go to the *Triggers* tab and click *New... -> On an event -> Custom -> New Event Trigger...*
	- Set the following filter options:
		- *Event logs*: *Windows Logs -> Security*
		- *Event ID*: 4688
		- *Keywords*: `Audit Success`
	- Go to the *XML* tab and click *Edit query manually*
	- Edit the query by adding the following line to the filter right before `</Select>`:
		- `and *[EventData[Data[@Name='NewProcessName'] and (Data='C:\Users\<username>\AppData\Roaming\Spotify\Spotify.exe')]]`
	- Go to the *Conditions* tab and disable `Start the task only if the computer is on AC power`
	- Go to the *Settings* tab and disable `Stop the task if it runs long than:`

### Setup: run program from log on until log off
With this setup, a custom task is created which is run at user log on and starts the Spotify Ad Muter program. This instance is run indefinitely until the user logs off.

- Create a Visual Basic Script (VBS) file, which is used to indirectly call the Python script:
```
Set WshShell = CreateObject("WScript.Shell")
Call WshShell.Run("python3 <absolute-dirpath>\spotify_ad_muter.py -p <absolute-filepath-to-cache-file>", 0)
Set WshShell = Nothing
```
- Create a task that runs the VBS file when the intended user logs on:
	- Run `taskschd.msc` and navigate to *Action -> Create Task...*
	- Provide the task name (e.g. "spotify-ad-muter-starter") and optionally a description 
	- Set it to run only when the current user is logged on
	- Go to the *Actions* tab and click *New...*
	- Set *Action* to "Start a program"
	- Link to the previously created VBS file
	- Go to the *Triggers* tab and click *New... -> At log on -> Specific user*
	- Set the intended user by clicking on *Change User* if needed
	- Go to the *Conditions* tab and disable `Start the task only if the computer is on AC power`
	- Go to the *Settings* tab and disable `Stop the task if it runs long than:`
