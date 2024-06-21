# smods_downloader
Smods.ru batch downloader
This script automatically downloads mods from smods.ru.
Instructions:

Put the script in a directory in which you want to download the mods.
Create a file named list.txt with the following format:

First line: Steam App ID (Open the game's workshop page, AppID is the number in the url after "/app/")
Following lines: Paste the workshop links, one per line. If the link is a collection, prepend it with a "!"


Run the script with python (Open terminal / cmd / powershell in the directory and type "py ./smods_dl.py"
Wait until done, the script reports it's progress.
