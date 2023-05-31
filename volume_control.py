import platform
if platform.system().lower() != "linux":
    from pycaw import pycaw
import re
import subprocess


class VolumeControl(object):

    __LINUX = 1
    __WINDOWS = 2
    __MAC = 3

    def __init__(self, logger):
        self.logger = logger
        # Store 'easy to read' variable with OS type
        kernel_str = platform.system().lower()
        if kernel_str == "linux":
            self.kernel = self.__LINUX
        elif kernel_str == "windows":
            self.kernel = self.__WINDOWS
        elif kernel_str == "darwin":
            self.kernel = self.__MAC
            self.logger("Error: Mac is currently unsupported")
            exit(1)
        else:
            self.logger("Error: unknown and unsupported system")
            exit(1)

    def get_system_volume(self):
        if self.kernel == self.__LINUX:
            return self.__get_alsa_system_volume()
        elif self.kernel == self.__WINDOWS:
            return self.__get_windows_system_volume()

    def set_system_volume(self, volume):
        if self.kernel == self.__LINUX:
            self.__set_alsa_system_volume(volume)
        elif self.kernel == self.__WINDOWS:
            self.__set_windows_system_volume(volume)

    # Use 'amixer' program to get general system volume
    def __get_alsa_system_volume(self):
        try:
            # Directly use the 'amixer' binary to get the system volume
            proc = subprocess.Popen(["/usr/bin/amixer", "sget", "Master"],
                shell=False, stdout=subprocess.PIPE)
            # Pass the program output to variable
            amixer_output = str(proc.communicate()[0])
            # Extract the first encountered volume value (front left volume) from the
            #   program output string using regular expression for "[<volume>%]"
            return int(re.search(r"\[([0-9]+)\%\]", amixer_output).group(1))
        except Exception as ex:
            self.logger.write("Error: Could not get ALSA system volume: %s" %
                str(ex))
            exit(1)

    # Use 'pycaw' to find and return 'Spotify' audio process volume
    def __get_windows_system_volume(self):
        try:
            # Iterate through all active audio processes to find 'Spotify'
            sessions = pycaw.AudioUtilities.GetAllSessions()
            volume = -1
            for session in sessions:
                audio_volume_interface = session._ctl.QueryInterface(pycaw.ISimpleAudioVolume)
                volume = int(audio_volume_interface.GetMasterVolume() * 100)
                if session.Process and "spotify" in session.Process.name().lower().split('.')[0]:
                    break
            if volume != -1:
                return volume
            error_message = "Could not find Spotify process"
        except Exception as ex:
            error_message = ex
        self.logger.write("Error: Could not get Windows system volume: %s" %
            str(error_message))
        exit(1)

    # Use 'amixer' program to set the general system volume
    def __set_alsa_system_volume(self, volume):
        try:
            # Directly use the 'amixer' binary to set the system volume
            proc = subprocess.Popen(
                ["/usr/bin/amixer", "sset", "Master", "%d%%" % volume],
                shell=False, stdout=subprocess.DEVNULL)
        except Exception as ex:
            self.logger.write("Error: Could not set ALSA system volume: %s" %
                str(ex))
            exit(1)

    # Use 'pycaw' to find and set the relative volume for the 'Spotify' audio process
    def __set_windows_system_volume(self, volume):
        try:
            # Iterate through all active audio processes to find 'Spotify'
            sessions = pycaw.AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and "spotify" in session.Process.name().lower().split('.')[0]:
                    audio_volume = session._ctl.QueryInterface(pycaw.ISimpleAudioVolume)
                    audio_volume.SetMasterVolume(volume / 100, None)
                    return
            error_message = "Could not find Spotify process"
        except Exception as ex:
            error_message = ex
        self.logger.write("Error: Could not set Windows system volume: %s" %
            str(error_message))
        exit(1)
