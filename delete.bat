@echo off
setlocal enabledelayedexpansion

REM Check if the path argument is provided.
if "%~1" == "" (
    echo Usage: %~nx0 "path_to_delete_from"
    exit /b 1
)

REM Set the path to delete from from the command-line argument.
set "delete_location=%~1"

REM Set the hardcoded filename for the text file containing relative paths.
set "file_list=to_delete.txt"

REM Check if the file exists.
if not exist "%file_list%" (
    echo File not found: "%file_list%"
    exit /b 1
)

REM Loop through each line in the text file.
for /f "usebackq delims=" %%a in ("%file_list%") do (
    REM Trim leading and trailing spaces from the path.
    set "file_path=%%a"
    
    REM Construct the full path to the file for deletion.
    set "full_path=!delete_location!\!file_path!"

    REM Check if the file exists and delete it.
    if exist "!full_path!" (
        echo Deleting: "!full_path!"
        del "!full_path!"
    ) else (
        echo File not found: "!full_path!"
    )
)

echo Deletion process completed.
exit /b 0
