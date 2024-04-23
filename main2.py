import os
import json
from datetime import datetime

BACKUPS_FOLDER_NAME_FORMAT = "backups_{0}"
CONFIG_FILE_NAME = "new_config.json"
FILE_INFO_FILE_NAME = "file_info.json"


class BackupManager:
    def __init__(self, backup_device_name):
        self.backup_device_name = backup_device_name
        self.backups_folder_name = BACKUPS_FOLDER_NAME_FORMAT.format(backup_device_name)
        self.new_snapshot_folder = os.path.join(self.backups_folder_name,
                                                datetime.now().strftime("%Y_%m_%d__%H_%M_%S__%f"))
        self.config_file_path = os.path.join(self.backups_folder_name, CONFIG_FILE_NAME)
        self.config_data = self._load_config()

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
        print(f"Initialized backup tracking for folders with snapshot at '{self.new_snapshot_folder}'.")

    def _get_previous_backup_info(self):
        # Retrieve the latest previous backup folder
        previous_backup_folder = self._get_latest_previous_backup_folder()
        if previous_backup_folder:
            previous_file_info_file = os.path.join(previous_backup_folder, FILE_INFO_FILE_NAME)
            if os.path.exists(previous_file_info_file):
                with open(previous_file_info_file, 'r') as f:
                    return json.load(f)
        return {}

    def _get_latest_previous_backup_folder(self):
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

        if snapshots:
            return snapshots[0]
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
            print(f"No tracked folders found for backup device '{self.backup_device_name}'.")


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

    if parsed_args.view_tracked_folders:
        tracked_folders = manager.get_tracked_folders()
        if tracked_folders:
            print(f"Tracked folders for backup device '{parsed_args.backup_device_name}':")
            for folder in tracked_folders:
                print(f"- {folder}")
        else:
            print(f"No tracked folders found for backup device '{parsed_args.backup_device_name}'.")
    elif parsed_args.add_folders:
        manager.add_folders(parsed_args.add_folders)
        print(f"Added folders to backup device '{parsed_args.backup_device_name}':")
        for folder in parsed_args.add_folders:
            print(f"- {folder}")
    elif parsed_args.remove_folders:
        manager.remove_folders(parsed_args.remove_folders)
        print(f"Removed folders from backup device '{parsed_args.backup_device_name}':")
        for folder in parsed_args.remove_folders:
            print(f"- {folder}")
    elif parsed_args.init:
        manager.init_backup(parsed_args.init)
    elif parsed_args.init_all:
        manager.init_all_backups()
    else:
        # create backup
        pass


if __name__ == "__main__":
    main()
