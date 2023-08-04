# BackupBuddy

BackupBuddy is a powerful and user-friendly backup utility that helps you safeguard your valuable data and files effortlessly. Whether you are an individual user or a business professional, BackupBuddy makes it easy to create backups, restore data, and ensure data protection against accidental data loss, hardware failure, or other unforeseen events.

## Features

- Might not delete all your files, I'm not responsible if it does.
  
## Installation

- Make sure you have python3 installed

## Usage

Run BackupBuddy from the command line or using the GUI (jk there's no GUI 😄)

1. Configure the folder that you want to backup (choose one folder per instance of the script).
   - ```python main.py --folder-to-backup "C:\folder\to\backup"```
2. Complete your first backup without using the script (the script won't really help here). Once that's done, you can run the script with ```--init``` flag to begin tracking changes. This will create a "backups" folder.
   - ```python main.py --init```
3. Go make some changes! You can add new files, modify existing files, and delete files.
4. Run the script without any flags:
   - ```python main.py```
5. A new folder will be created in the backups folder containing a log file (if you need it) and more importantly a "to_tranfer" folder. This is the folder that should be transferred to your backup device.
6. Once you have transferred the "to_transfer" folder, you need to perform two steps:
   - Copy the contents of the additions folder to your backup location. Allow file explorer to merge.
   - Run the delete.bat script directly from it's location, providing full path to the backup location as an argument. This will delete all the files that you have deleted since the last backup. You can view these files prior to running the script in "to_delete.txt" to ensure you're not deleting anything you want to keep.
     - ```delete.bat "C:\path\to\backup\location"```

## Support

If you have any questions, feedback, or support inquiries, you are welcome to relay them to your grandma as it will have the same effect as contacting me and will save me from having to pretend I care.

---

© 2023 BackupBuddy. All rights reserved.
