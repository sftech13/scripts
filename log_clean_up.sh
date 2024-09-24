import os
import glob
import logging

# Define the log directory
LOG_DIR = '/home/sftech13/logs/'

# Setup logging for this cleanup script (if desired)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, 'cleanup_script.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def delete_log_files(log_directory):
    """Deletes all log files in the specified log directory."""
    # Look for files with .log extension in the specified directory
    log_files = glob.glob(os.path.join(log_directory, '*.log'))

    if not log_files:
        logging.info("No log files found to delete.")
        print("No log files found to delete.")
        return

    for log_file in log_files:
        try:
            os.remove(log_file)
            logging.info(f"Deleted log file: {log_file}")
            print(f"Deleted log file: {log_file}")
        except Exception as e:
            logging.error(f"Error deleting log file {log_file}: {e}")
            print(f"Error deleting log file {log_file}: {e}")

# Run the cleanup script
delete_log_files(LOG_DIR)

