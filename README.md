# BackupBuddy

BackupBuddy is a powerful and user-friendly backup utility that helps you safeguard your valuable data and files
effortlessly. Whether you are an individual user or a business professional, BackupBuddy makes it easy to create
backups, restore data, and ensure data protection against accidental data loss, hardware failure, or other unforeseen
events.

## Features

- Enables simultaneous tracking of multiple backup locations.
- Supports tracking multiple folders, offering flexibility to track different folders for each backup location as
  needed.

## Requirements

- Python3

## Usage

Run BackupBuddy from the command line or using the GUI (jk there's no GUI 😄)

### Managing tracked folders:

Each backup location has its own list of folders that it tracks. The following flags may be used to interact with the
list:

- **Adding folders**:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME --add-folders PATH/TO/TRACK ANOTHER/PATH/TO/TRACK
```

- **Removing folders**:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME --remove-folders PATH/TO/REMOVE ANOTHER/PATH/TO/REMOVE
```

- **Viewing tracked folders**:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME --view-tracked-folders
```

### Initializing Backup Tracking

After adding folders to track, initialize the backup by copying the folders to the backup location and running the
following command:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME --init-all
```

Alternatively, you can specify specific folders to initialize like so:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME --init PATH/TO/INITIALIZE ANOTHER/PATH/TO/INITIALIZE
```

This step makes BackupBuddy take a snapshot of the current state of the folders in order to track changes from this
point onward.

### Creating Snapshot for Backup

To create the files necessary for synchronizing your backup with new changes that you have made in your tracked folders,
simply run:

```commandline
python main.py --backup-location-name BACKUP_LOCATION_NAME
```

This will generate a ```to_transfer``` folder within the ```backups``` directory. It will also take a snapshot of the
current state of your folders.

### Synchronizing Changes

Transfer the ```to_transfer``` folder to the backup location and navigate to it.

1. First, open the ```additions``` folder and copy the folders to the corresponding locations of the old backup. Allow
   file explorer to merge.
2. Next, notice that each folder has a corresponding ```{FOLDER_NAME}_deleted_paths.txt``` file. Run the delete.bat
   script for each folder from which files have been deleted, like so:
   ```commandline
   delete.bat PATH\TO\BACKED\UP\FOLDER {FOLDER_NAME}_deleted_paths.txt
   ```

Your backed up folders should now be up-to-date.

---

© 2024 BackupBuddy. All rights reserved.
