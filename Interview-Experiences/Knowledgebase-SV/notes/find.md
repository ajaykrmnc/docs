## Find command in linux

- search for files and directories (recursively) based on various criterias

- `find [path] [expression]` 
  
  - [path]:  The directory where the search will be started
  
  - [expression]: Filter criteria
  
  - when using `-name -iname` as criteria * is supported for wildcard

- `find /home/user -name "example.txt"` find a file with following name in /home/user directory

- `find /home/user -iname "example.txt"`: case insensitive search `iname`

- `find /path -type f`: find only files not directories

- `find /path -type d`: find only directories

- `find /path -type l`: find symbolic links

- `find / -size +100M`: find files greater than 100MB

- `find / -size -5k`: find files smaller than 5KB

- `find /home -type f -perm 644`: find files with permission mode

- `find /home -type f -mtime -7`: find files modified in last 7 days

- `find /home -type f -atime -2`: find files accessed in last 2 days

- `find /path -type f -name "*.log" -exec rm {} +`
  
  - `-exec`: executes the given command
  
  - `{}`: placeholder for the attributes
  
  - `+`: end of the command

- `find /path -type f -empty`: find empty files (use d for directories)

- `find /home -type f -name "*.log" -exec grep -i "error" {} +`: searching inside files (find all the log files which contain "error") 

- `find /var/log -type f -name "*.log" | xargs rm`: xargs takes a list and passes each element as arguments to another command
