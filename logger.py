import datetime
import sys


class Logger(object):

    def __init__(self, log_file):
        self.log = None
        if log_file != None:
            try:
                self.log = open(log_file, "w", buffering=1)
            except Exception as ex:
                print("Error: Could not create or open log file '%s': %s" %
                    (log_file, str(ex)))
                exit(1)
        self.terminal = sys.stdout

    def __del__(self):
        if self.log != None:
            self.log.close()

    def write(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_message = "%s:  %s\n" % (timestamp, message)
        self.terminal.write(total_message)
        if self.log != None:
            self.log.write(total_message)
