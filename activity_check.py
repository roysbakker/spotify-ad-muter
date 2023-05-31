import os
import psutil
import spotipy


class ActivityCheck(object):

    def __init__(self, logger, spotipy_obj):
        self.logger = logger
        self.spotipy_obj = spotipy_obj

    def is_target_device_active(self, target_device_name):
        # Attempt to extract information about user's Spotify devices
        try:
            spotify_devices = self.spotipy_obj.devices()['devices']
        # Report specific Spotify API error
        except spotipy.client.SpotifyException as ex:
            self.logger.write("Error: {HTTP status = %d; HTTP message = %s;}" %
                (ex.http_status, ex.msg))
            return False
        # Report any other random error
        except Exception as ex:
            self.logger.write("Error: unexpected error occurred: %s" % str(ex))
            return False
        # Check if the target Spotify device is in the user's device list
        for device in spotify_devices:
            if device['name'].lower() == target_device_name:
                return device['is_active']
        return False

    def is_spotify_active(self):
        is_active = False
        # Iterate through all active processes
        for p in psutil.process_iter(attrs=['name']):
            # Check if Spotify is present in list of active processes
            #   or otherwise running, sleeping, or a state in between
            if "spotify" in p.name().lower().split('.')[0] and \
                    (p.status() == psutil.STATUS_RUNNING or
                    p.status() == psutil.STATUS_SLEEPING or
                    p.status() == psutil.STATUS_WAKING):
                is_active = True
                break
        return is_active

    def lock_activities(self, lock_file_path):
        # Check if lock file already exists
        if os.path.isfile(lock_file_path) == True:
            # If it exists, read the PID contained within
            try:
                lock_file = open(lock_file_path, "r")
                for line in lock_file:
                    pid = int(line)
                    break
            except Exception as ex:
                self.logger.write("Error: Could not read lock file '%s': %s" %
                    (lock_file_path, str(ex)))
                exit(1)
            # Check if the process that created the lock file still exists based on
            #   its PID and return False if so, otherwise, remove the lock file
            if psutil.pid_exists(pid) == True:
                lock_file.close()
                return False
            else:
                lock_file.close()
                os.remove(lock_file_path)
        # If no other instance of this program is running, create a lock file
        try:
            lock_file = open(lock_file_path, "w")
            lock_file.write(str(os.getpid()))
            lock_file.close()
            return True
        except Exception as ex:
            self.logger.write("Error: Could not read lock file '%s': %s" %
                (lock_file_path, str(ex)))
            exit(1)

    def unlock_activities(self, lock_file_path):
        # Check if this program's lock file still exists, and if so remove it
        if os.path.isfile(lock_file_path) == True:
            try:
                os.remove(lock_file_path)
            except Exception as ex:
                self.logger.write("Error: Could not find lock file to delete '%s': %s" %
                    (lock_file_path, str(ex)))
                exit(1)
