import logging
import os
import json
import shutil
from datetime import datetime

BACKUPS_FOLDER_NAME_FORMAT = "backups\\backups_{0}"
CONFIG_FILE_NAME = "new_config.json"
FILE_INFO_FILE_NAME = "file_info.json"
LOG_FILE_PATH = "logs"
DELETE_BAT_FILE_NAME = "delete.bat"


class BackupManager:
    def __init__(self, backup_device_name):
        self.backup_device_name = backup_device_name
        self.backups_folder_name = BACKUPS_FOLDER_NAME_FORMAT.format(backup_device_name)
        self.new_snapshot_folder = os.path.join(self.backups_folder_name,
                                                datetime.now().strftime("%Y_%m_%d__%H_%M_%S__%f"))
        self.config_file_path = os.path.join(self.backups_folder_name, CONFIG_FILE_NAME)
        self.config_data = self._load_config()
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    '''
    Config management
    '''

    def _load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, 'r') as f:
                return json.load(f)
        else:
            return {}

    def _save_config(self):
        os.makedirs(self.backups_folder_name, exist_ok=True)
        with open(self.config_file_path, 'w') as f:
            json.dump(self.config_data, f, indent=4)

    def get_tracked_folders(self):
        if 'backup_locations' in self.config_data and self.backup_device_name in self.config_data['backup_locations']:
            return self.config_data['backup_locations'][self.backup_device_name]
        else:
            return []

    def add_folders(self, folders_to_add):
        if 'backup_locations' not in self.config_data:
            self.config_data['backup_locations'] = {}
        if self.backup_device_name not in self.config_data['backup_locations']:
            self.config_data['backup_locations'][self.backup_device_name] = []

        self.config_data['backup_locations'][self.backup_device_name].extend(folders_to_add)
        self._save_config()

    def remove_folders(self, folders_to_remove):
        if 'backup_locations' in self.config_data and self.backup_device_name in self.config_data['backup_locations']:
            current_folders = self.config_data['backup_locations'][self.backup_device_name]
            updated_folders = [folder for folder in current_folders if folder not in folders_to_remove]
            self.config_data['backup_locations'][self.backup_device_name] = updated_folders
            self._save_config()

    '''
    Initializing
    '''

    def init_backup(self, folders_to_track):
        os.makedirs(self.new_snapshot_folder)

        file_info = {}

        # Gather file info for newly initialized folders
        for folder in folders_to_track:
            folder_info = self._gather_file_info(folder)
            file_info[folder] = folder_info

        # Get file info from the previous backup (if available)
        previous_backup_info = self._get_previous_backup_info()

        # Include file info from previous backup for existing folders not in the current initialization
        for folder, info in previous_backup_info.items():
            if folder not in file_info:
                file_info[folder] = info

        # Save the merged file info to the new backup folder
        self._save_file_info(file_info, os.path.join(self.new_snapshot_folder, FILE_INFO_FILE_NAME))
        self.logger.info(f"Initialized backup tracking for folders with snapshot at '{self.new_snapshot_folder}'.")

    def _get_previous_backup_info(self):
        # Retrieve the latest previous backup folder
        previous_backup_folder = self._get_folder_with_latest_snapshot()
        if previous_backup_folder:
            previous_file_info_file = os.path.join(previous_backup_folder, FILE_INFO_FILE_NAME)
            if os.path.exists(previous_file_info_file):
                with open(previous_file_info_file, 'r') as f:
                    return json.load(f)
        return {}

    def _get_folder_with_latest_snapshot(self):
        # Get a list of all snapshots
        snapshots = [os.path.join(self.backups_folder_name, file) for file in os.listdir(self.backups_folder_name)]

        # Filter out files that aren't folders
        snapshots = [file for file in snapshots if
                     os.path.isdir(file)]

        # Filter out the new snapshot folder if it exists
        snapshots = [folder for folder in snapshots
                     if folder != self.new_snapshot_folder]

        # Sort in reverse
        snapshots = sorted(snapshots, reverse=True)

        for folder in snapshots:
            if FILE_INFO_FILE_NAME in os.listdir(folder):
                return folder
        return None

    def _gather_file_info(self, root_folder):
        file_info = {}
        for folder_path, _, file_names in os.walk(root_folder):
            for file_name in file_names:
                file_path = os.path.join(folder_path, file_name)
                relative_file_path = os.path.relpath(file_path, start=root_folder)
                file_mod_time = os.path.getmtime(file_path)
                file_info[relative_file_path] = file_mod_time
        return file_info

    def _save_file_info(self, file_info, output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(file_info, f, indent=4)

    def init_all_backups(self):
        if 'backup_locations' in self.config_data and self.backup_device_name in self.config_data['backup_locations']:
            folders_to_track = self.config_data['backup_locations'][self.backup_device_name]
            self.init_backup(folders_to_track)
        else:
            self.logger.error(f"No tracked folders found for backup device '{self.backup_device_name}'.")

    '''
    Backups
    '''

    def backup(self):
        try:
            # Ensure all configured folders have been initialized
            previous_backup_info = self._get_previous_backup_info()

            initialized_folders = set(previous_backup_info.keys())
            configured_folders = set(self.get_tracked_folders())

            if not configured_folders:
                self.logger.error("No folders configured for backup.")
                return

            uninitialized_folders = configured_folders - initialized_folders

            if uninitialized_folders:
                self.logger.error(f"The following folders have not been initialized: {uninitialized_folders}")
                return

            to_transfer_path = os.path.join(self.new_snapshot_folder, "to_transfer")
            os.makedirs(to_transfer_path)

            file_info = {}

            # Perform backup for each folder
            for folder in configured_folders:
                previous_snapshot_info = previous_backup_info[folder]

                file_info[folder] = self._gather_file_info(folder)
                additions_path = os.path.join(to_transfer_path, os.path.basename(folder))

                # Copy new or modified files to additions folder
                for relative_file_path, modification_time in file_info[folder].items():
                    if (relative_file_path not in previous_snapshot_info or
                            modification_time != previous_snapshot_info[relative_file_path]):
                        source_file_path = os.path.join(folder, relative_file_path)
                        destination_file_path = os.path.join(additions_path, relative_file_path)

                        destination_dir = os.path.dirname(destination_file_path)
                        os.makedirs(destination_dir, exist_ok=True)

                        shutil.copy2(source_file_path, destination_file_path)
                        self.logger.debug(f"File '{source_file_path}' copied to '{destination_file_path}'.")

                # Write deleted file paths to a file
                deleted_paths_file = os.path.join(to_transfer_path, f"{os.path.basename(folder)}_deleted_paths.txt")
                with open(deleted_paths_file, "w+") as f:
                    for relative_file_path in previous_snapshot_info:
                        if relative_file_path not in file_info[folder]:
                            f.write(relative_file_path + "\n")

            self._copy_file(source_file=DELETE_BAT_FILE_NAME,
                            destination_file=to_transfer_path)

            # Save new snapshot file information
            self._save_file_info(file_info, os.path.join(self.new_snapshot_folder, FILE_INFO_FILE_NAME))

            self.logger.info("Backup completed successfully.")

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")

    def _copy_file(self, source_file, destination_file):
        """
        Copies a file from source to destination.
        source_file: The path to the source file.
        source_file type: string
        destination_file: The path to the destination file.
        destination_file type: string
        logger: The logger object to log messages.
        logger type: logging.Logger
        return: None
        """
        try:
            shutil.copy2(source_file, destination_file)
            self.logger.debug(f"File '{source_file}' copied to '{destination_file}' successfully.")
        except FileNotFoundError:
            self.logger.debug("File not found.")
        except shutil.SameFileError:
            self.logger.debug("Source and destination are the same file.")
        except PermissionError:
            self.logger.debug("Permission error while copying the file.")
        except Exception as e:
            self.logger.debug(f"An error occurred: {e}")


def setup_logging(log_file):
    logger = logging.getLogger('my_logger')
    logger.setLevel(logging.DEBUG)

    # Create a file handler for the log file
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Create a console handler to log messages to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Log messages above INFO level to console
    console_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def main():
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("--backup-device-name", type=str,
                        help="The name of the backup device.", required=True)
    parser.add_argument("--view-tracked-folders", action="store_true",
                        help="View the tracked folders for the specified backup device.")
    parser.add_argument("--add-folders", nargs='+',
                        help="Add new folder paths to track for the specified backup device.")
    parser.add_argument("--remove-folders", nargs='+',
                        help="Remove folder paths from tracking for the specified backup device.")
    parser.add_argument("--init", nargs='+',
                        help="Initialize backup tracking with snapshot for specific folders.")
    parser.add_argument("--init-all", action="store_true",
                        help="Initialize backup tracking with snapshot for all tracked folders.")

    parsed_args = parser.parse_args()

    manager = BackupManager(parsed_args.backup_device_name)
    os.makedirs(os.path.join(manager.backups_folder_name, LOG_FILE_PATH), exist_ok=True)
    logger = setup_logging(log_file=os.path.join(manager.backups_folder_name, LOG_FILE_PATH,
                                                 os.path.basename(manager.new_snapshot_folder) + ".log"))
    manager.set_logger(logger)

    if parsed_args.view_tracked_folders:
        tracked_folders = manager.get_tracked_folders()
        if tracked_folders:
            logger.info(f"Tracked folders for backup device '{parsed_args.backup_device_name}':")
            for folder in tracked_folders:
                logger.info(f"- {folder}")
        else:
            logger.info(f"No tracked folders found for backup device '{parsed_args.backup_device_name}'.")
    elif parsed_args.add_folders:
        manager.add_folders(parsed_args.add_folders)
        logger.info(f"Added folders to backup device '{parsed_args.backup_device_name}':")
        for folder in parsed_args.add_folders:
            logger.info(f"- {folder}")
    elif parsed_args.remove_folders:
        manager.remove_folders(parsed_args.remove_folders)
        logger.info(f"Removed folders from backup device '{parsed_args.backup_device_name}':")
        for folder in parsed_args.remove_folders:
            logger.info(f"- {folder}")
    elif parsed_args.init:
        manager.init_backup(parsed_args.init)
    elif parsed_args.init_all:
        manager.init_all_backups()
    else:
        manager.backup()


if __name__ == "__main__":
    main()
