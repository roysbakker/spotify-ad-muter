import getpass
import os
import platform
import socket
import spotipy


class ProgramConfig(object):

    def __init__(self,
            automatic_closing=False,
            ad_volume_percentage=0,
            target_device_name="",
            auth_cache_path="",
            log_file_path=""):
        # Get general system information
        username_str = getpass.getuser()
        hostname_str = socket.gethostname()
        kernel_str = platform.system().lower()

        # Set flag if this application must close itself if Spotify is found
        #   not to be an active process on this machine
        self.AUTOMATIC_CLOSING = automatic_closing

        # Set the ad volume to a round integer and within the range [0-100]
        self.AD_VOLUME_PERCENTAGE = \
            min([100, max([0, round(ad_volume_percentage, 0)])])

        # Set the target device name as the host's name by default
        self.TARGET_DEVICE_NAME = target_device_name
        if target_device_name == None:
            self.TARGET_DEVICE_NAME = socket.gethostname().lower()

        # Set default location for Spotify authorization information storage
        self.AUTH_CACHE_PATH = auth_cache_path
        if auth_cache_path == None:
            if kernel_str == "linux":
                self.AUTH_CACHE_PATH = "/home/%s/Documents/.cache" % username_str
            elif kernel_str == "windows":
                self.AUTH_CACHE_PATH = "C:\\Users\\%s\\Documents\\.cache" % username_str
            elif kernel_str == "darwin":
                print("Error: Mac is currently unsupported")
                exit(1)
            else:
                print("Error: unknown and unsupported system")
                exit(1)
        dirname = os.path.dirname(self.AUTH_CACHE_PATH)
        if os.path.exists(dirname) == False:
            print("Error: specified authentication cache directory does not exist: %s" %
                  dirname)
            exit(1)
        # Make the authentication cache path absolute
        self.AUTH_CACHE_PATH = os.path.abspath(self.AUTH_CACHE_PATH)

        # Set default location for log file
        self.LOG_FILE_PATH = log_file_path
        if log_file_path == None:
            if kernel_str == "linux":
                self.LOG_FILE_PATH = "/tmp/spotify-ad-muter.log"
            elif kernel_str == "windows":
                self.LOG_FILE_PATH = "%s\\spotify-ad-muter.log" % os.environ['TEMP']
            elif kernel_str == "darwin":
                print("Error: Mac is currently unsupported")
                exit(1)
            else:
                print("Error: unknown and unsupported system")
                exit(1)
        dirname = os.path.dirname(self.LOG_FILE_PATH)
        if os.path.exists(dirname) == False:
            print("Error: specified log directory does not exist: %s" %
                  dirname)
            exit(1)
        # Make the log file path absolute
        self.LOG_FILE_PATH = os.path.abspath(self.LOG_FILE_PATH)

        # set location for the lock file
        if kernel_str == "linux":
            self.LOCK_FILE_PATH = "/tmp/spotify-ad-muter.lock"
        elif kernel_str == "windows":
            self.LOCK_FILE_PATH = "%s\\spotify-ad-muter.lock" % os.environ['TEMP']
        elif kernel_str == "darwin":
            print("Error: Mac is currently unsupported")
            exit(1)
        else:
            print("Error: unknown and unsupported system")
            exit(1)

        # Store custom Spotify App information
        self.SCOPE = "user-read-playback-state"

        # Initialize spotify authentication manager, which shows a browser login dialog
        #   if not already logged in
        self.CLIENT_CREDENTIAL_MANAGER = spotipy.oauth2.SpotifyPKCE(
                scope = self.SCOPE,
                open_browser = True,
                cache_handler=spotipy.CacheFileHandler(
                    cache_path=self.AUTH_CACHE_PATH)
            )    
