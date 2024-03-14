import os
import pickle
import shutil
import argparse
import json
import sys
from datetime import datetime
import logging

BACKUPS_FOLDER_NAME_FORMAT = "backups_{0}"
TO_TRANSFER_FOLDER_NAME = "to_transfer"
FILE_INFO_FILE_NAME = "file_info.pkl"
DELETE_BAT_FILE_NAME = "delete.bat"
LOG_FILE_NAME = "app.log"
TO_DELETE_FILE_NAME = "to_delete.txt"


def gather_file_info(root_folder):
    """
    Gathers file information recursively from a given root folder.
    root_folder: The root folder from which to start gathering file information.
    root_folder type: string
    return: A dictionary containing file information with relative paths as keys and modification times as values.
    return type: dict
    """
    file_info = {}

    for folder_path, _, file_names in os.walk(root_folder):
        for file_name in file_names:
            file_path = os.path.join(folder_path, file_name)
            relative_file_path = os.path.relpath(file_path, start=root_folder)
            file_mod_time = os.path.getmtime(file_path)
            file_info[relative_file_path] = file_mod_time

    return file_info


def save_file_info_to_file(file_info, output_file):
    """
    Saves file information to a pickle file.
    file_info: The file information to be saved.
    file_info type: dict
    output_file: The path to the output file.
    output_file type: string
    return: None
    """
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'wb') as f:
        pickle.dump(file_info, f)


def load_file_info_from_file(input_file):
    """
    Loads file information from a pickle file.
    input_file: The path to the input file.
    input_file type: string
    return: The loaded file information.
    return type: dict
    """
    with open(input_file, 'rb') as f:
        file_info = pickle.load(f)
    return file_info


def copy_file(source_file, destination_file, logger):
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
        logger.debug(f"File '{source_file}' copied to '{destination_file}' successfully.")
    except FileNotFoundError:
        logger.debug("File not found.")
    except shutil.SameFileError:
        logger.debug("Source and destination are the same file.")
    except PermissionError:
        logger.debug("Permission error while copying the file.")
    except Exception as e:
        logger.debug(f"An error occurred: {e}")


def load_config(config_file):
    """
    Loads configuration data from a JSON file.
    config_file: The path to the configuration file.
    config_file type: string
    return: The loaded configuration data.
    return type: dict
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config_file, config_data):
    """
    Saves configuration data to a JSON file.
    config_file: The path to the configuration file.
    config_file type: string
    config_data: The configuration data to be saved.
    config_data type: dict
    return: None
    """
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=4)


def get_previous_backup_file_info(backups_folder_name):
    """
    Gets file information from the previous backup folder.
    backups_folder_name: The name of the backups folder.
    backups_folder_name type: string
    return: File information from the previous backup folder.
    return type: dict
    """
    # Get a list of all folders in the directory
    folders = [f for f in os.listdir(backups_folder_name) if os.path.isdir(os.path.join(backups_folder_name, f))]

    # Sort the folders by name (in ascending order by default)
    sorted_folders = sorted(folders)

    if sorted_folders:
        # Choose the last folder in the sorted list (the one with the greatest name)
        try:
            latest_folder = os.path.join(backups_folder_name, sorted_folders[-2])
        except IndexError:
            raise PreviousBackupNotFoundException()
        return load_file_info_from_file(os.path.join(latest_folder, FILE_INFO_FILE_NAME))
    else:
        raise FileNotFoundError


def update_config(config_file, config_data, parsed_args):
    config_data["folder_to_backup"] = parsed_args.folder_to_backup
    save_config(config_file, config_data)


def init(logger, config_data, backup_folder):
    """
    Initializes the backup process.
    logger: The logger object to log messages.
    logger type: logging.Logger
    config_data: The configuration data.
    config_data type: dict
    backup_folder: The path to the backup folder.
    backup_folder type: string
    return: None
    """
    file_info = gather_file_info(config_data["folder_to_backup"])
    save_file_info_to_file(file_info, os.path.join(backup_folder, FILE_INFO_FILE_NAME))
    logger.debug(f"Completed init - created initial backup folder: {backup_folder}")


class PreviousBackupNotFoundException(Exception):
    pass


def backup(logger, config_data, backup_folder, backups_folder_name):
    """
    Performs the backup process.
    logger: The logger object to log messages.
    logger type: logging.Logger
    config_data: The configuration data.
    config_data type: dict
    backup_folder: The path to the backup folder.
    backup_folder type: string
    backups_folder_name: The name of the backups folder.
    backups_folder_name type: string
    return: None
    """
    try:
        previous_backup_file_info = get_previous_backup_file_info(backups_folder_name)
    except FileNotFoundError:
        raise PreviousBackupNotFoundException()

    folder_to_backup = config_data["folder_to_backup"]
    to_transfer_path = os.path.join(backup_folder, TO_TRANSFER_FOLDER_NAME)
    additions_path = os.path.join(to_transfer_path, "additions")

    os.makedirs(to_transfer_path)

    file_info = gather_file_info(folder_to_backup)

    # Copy new files to additions folder.
    logger.debug("Starting to copy additions")
    for relative_file_path, modification_time in file_info.items():
        if relative_file_path not in previous_backup_file_info or \
                modification_time != previous_backup_file_info[relative_file_path]:

            source_file_path = os.path.join(folder_to_backup, relative_file_path)
            destination_file_path = os.path.join(additions_path, relative_file_path)

            destination_file_path_dir, _ = os.path.split(destination_file_path)
            os.makedirs(destination_file_path_dir, exist_ok=True)

            copy_file(source_file=source_file_path,
                      destination_file=destination_file_path,
                      logger=logger)

    # Make file with paths that have been deleted since the last backup.
    logger.debug(f"Starting to write file paths to {TO_DELETE_FILE_NAME}")
    with open(os.path.join(to_transfer_path, TO_DELETE_FILE_NAME), "w+") as to_delete_file:
        for relative_file_path in previous_backup_file_info:
            if relative_file_path not in file_info:
                to_delete_file.write(relative_file_path + "\n")

    logger.debug(f"Copying {DELETE_BAT_FILE_NAME} to {to_transfer_path}")
    copy_file(source_file=DELETE_BAT_FILE_NAME,
              destination_file=to_transfer_path,
              logger=logger)

    save_file_info_to_file(file_info, os.path.join(backup_folder, FILE_INFO_FILE_NAME))


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
    parser = argparse.ArgumentParser()

    parser.add_argument("--backup-device-name", type=str,
                        help="The name of the backup device.", required=True)
    parser.add_argument("--folder-to-backup", type=str,
                        help="Please provide full path. Needs to be provided only once.")
    parser.add_argument("--init", action="store_true",
                        help="Run this once you have configured everything and backed everything up. Program will start tracking from here.")

    parsed_args = parser.parse_args()

    if (parsed_args.folder_to_backup and parsed_args.backup_device_name) or (parsed_args.init and parsed_args.backup_device_name) or parsed_args.backup_device_name:
        pass
    else:
        parser.error("Invalid combination of arguments.")

    backups_folder_name = BACKUPS_FOLDER_NAME_FORMAT.format(parsed_args.backup_device_name)

    config_file = os.path.join(backups_folder_name, "config.json")
    config_data = load_config(config_file)

    if parsed_args.folder_to_backup:
        update_config(config_file, config_data, parsed_args)
    elif "folder_to_backup" not in config_data:
        print("Please provide --folder-to-backup flag.")
    else:
        backup_folder = os.path.join(backups_folder_name, datetime.now().strftime("%Y_%m_%d__%H_%M_%S__%f"))
        os.makedirs(backup_folder)
        logger = setup_logging(log_file=os.path.join(backup_folder, LOG_FILE_NAME))
        if parsed_args.init:
            init(logger, config_data, backup_folder)
            logger.info("Finished init! You can now backup :)")
        else:
            try:
                backup(logger, config_data, backup_folder, backups_folder_name)
                logger.info("Created backup!")
            except PreviousBackupNotFoundException as e:
                logger.error("Previous backup not found. Please make sure to run script with --init flag before creating first backup.")


if __name__ == "__main__":
    main()
