# Import python libraries
import argparse
import atexit
import spotipy
import time
# Import user modules
import activity_check
import logger
import program_config
import volume_control


# Set program constants
SLEEP_PERIOD_ERROR_S = 60
SLEEP_PERIOD_PAUSED_MIN_S = 5
SLEEP_PERIOD_PAUSED_MAX_S = 20
SLEEP_PERIOD_PLAYING_TRACK_S = 10
SLEEP_PERIOD_PLAYING_AD_S = 1


if __name__ == "__main__":
    # Specify the format of the command line arguments
    arg_parser = argparse.ArgumentParser(
        prog="spotify_ad_muter",
        description="Spotify Ad Muter turns the system volume down if an ad " +
            "is playing on the target device's Spotify.")
    arg_parser.add_argument('-c', '--auto_close',
        action='store_true',
        help="Close this app automatically if Spotify is not an active " +
            "process on this machine",
        dest='automatic_closing')
    arg_parser.add_argument('-a', '--ad_volume',
        default=10, type=int,
        help="Percentage of normal volume at which ads will play [0-100]",
        dest='ad_volume_percentage')
    arg_parser.add_argument('-t', '--dev_name',
        default=None,
        help="Device name of the target device on which Spotify is running",
        dest='target_device_name')
    arg_parser.add_argument('-p', '--cache_path',
        default=None,
        help="File path of the file in which to cache authentication " +
            "information",
        dest='auth_cache_path')
    arg_parser.add_argument('-l', '--log_path',
        default=None,
        help="File path of the file in which to store program log information",
        dest='log_file_path')
    # Parse the command line arguments
    args = arg_parser.parse_args()
    # Validate the arguments as and generate a program configuration
    config = program_config.ProgramConfig(
        args.automatic_closing,
        args.ad_volume_percentage,
        args.target_device_name,
        args.auth_cache_path,
        args.log_file_path)

    # Create a logger object and redirect STDOUT to the object for writes,
    #   causing all 'print' statements to print both to STDOUT and the log file
    log = logger.Logger(config.LOG_FILE_PATH)
    # Initialize Spotify client object
    try:
        sp = spotipy.Spotify(
            auth_manager=config.CLIENT_CREDENTIAL_MANAGER,
            requests_timeout=30,
            backoff_factor=0.6)
    except Exception as ex:
        logger.write("Error: Could not initialize Spotify object: %s" % str(ex))
        exit(1)
    # Create activity checker object for tracking process and device activity
    activity_checker = activity_check.ActivityCheck(log, sp)
    # Check if instance of this program is already running:
    #   > if true, exit
    #   > else, create a lock file
    if (activity_checker.lock_activities(config.LOCK_FILE_PATH) == False):
        log.write("Error: Instance already running")
        exit(1)
    # Register the unlock function as function handler on program exit
    atexit.register(activity_checker.unlock_activities, config.LOCK_FILE_PATH)
    # Create volume control object for system independent volume control
    volume_controller = volume_control.VolumeControl(log)
    # Get initial system volume
    normal_volume = volume_controller.get_system_volume()
    is_ad = False

    while config.AUTOMATIC_CLOSING == False or activity_checker.is_spotify_active() == True:
        # Reset next sleep period
        sleep_period_s = SLEEP_PERIOD_ERROR_S
        # Check if target device is currently active
        if activity_checker.is_target_device_active(config.TARGET_DEVICE_NAME) == False:
            if is_ad == True:
                volume_controller.set_system_volume(normal_volume)
                is_ad = False
            log.write("Error: Target device is not currently active")
            time.sleep(sleep_period_s)
            continue
        # Attempt to extract current playback state information
        try:
            playback_state = sp.currently_playing(additional_types='track,episode')
        # Report specific Spotify API error
        except spotipy.client.SpotifyException as ex:
            if is_ad == True:
                volume_controller.set_system_volume(normal_volume)
                is_ad = False
            log.write("Error: {HTTP status = %d; HTTP message = %s;}" %
                (ex.http_status, ex.msg))
            time.sleep(sleep_period_s)
            continue
        # Report any other random error
        except Exception as ex:
            if is_ad == True:
                volume_controller.set_system_volume(normal_volume)
                is_ad = False
            log.write("Error: unexpected error occurred: %s" % str(ex))
            time.sleep(sleep_period_s)
            continue
        # Print error if playback state is empty
        if playback_state == None:
            if is_ad == True:
                volume_controller.set_system_volume(normal_volume)
                is_ad = False
            log.write("No playback state found")
            time.sleep(sleep_period_s)
            continue

        # Extract useful information from obtained Spotify playback state
        currently_playing_type = playback_state['currently_playing_type']
        is_playing = playback_state['is_playing']
        # If Spotify is currently playing a track...
        if currently_playing_type == "track" or currently_playing_type == "episode":
            # If on the iteration before an ad was playing, restore the system volume
            if is_ad == True:
                # Add a small delay before resetting the volume, playback on device may
                #   lag slightly compared to the Spotify API requests
                time.sleep(1)
                volume_controller.set_system_volume(normal_volume)
                is_ad = False
            track_progress_ms = playback_state['progress_ms']
            track_duration_ms = playback_state['item']['duration_ms']
            track_remaining_s = (track_duration_ms - track_progress_ms) / 1000
            # Set sleep period based on if track is paused or, if active, its
            #   remaining play time
            if is_playing == False:
                sleep_period_s = max([SLEEP_PERIOD_PAUSED_MIN_S,
                    min([SLEEP_PERIOD_PAUSED_MAX_S, track_remaining_s])])
                log.write("track is active, but paused")
            else:
                sleep_period_s = min([SLEEP_PERIOD_PLAYING_TRACK_S, track_remaining_s])
                log.write("track is active, with %ds remaining" % track_remaining_s)
        # If Spotify is currently playing an ad...
        elif currently_playing_type == "ad":
            # If on the iteration before a track was playing, reduce the system volume
            if is_ad == False:
                # Save the current volume to restore later after ads are done playing
                normal_volume = volume_controller.get_system_volume()
                volume_controller.set_system_volume(config.AD_VOLUME_PERCENTAGE)
                is_ad = True
            # Set sleep period based on if ad is paused or not
            if is_playing == False:
                sleep_period_s = SLEEP_PERIOD_PAUSED_MIN_S
                log.write("ad is active, but paused")
            else:
                sleep_period_s = SLEEP_PERIOD_PLAYING_AD_S
                log.write("ad is active")
        else:
            log.write("Error: Unknown type playing")
        # Suspend program for previously determined period
        time.sleep(sleep_period_s)

    # Exit gracefully if Spotify is not running on this device by returning
    #   the system volume to normal and quiting execution
    log.write("Spotify is not a running process; quitting...")
    volume_controller.set_system_volume(normal_volume)
    exit(0)
