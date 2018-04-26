# bus report card

Python wrapper to query XML based realtime bus locations.  Currently supports NJ.

Some notebooks have been added as examples.


## Usage


### Testing
```
python2 buswatcher.py -s nj --save-raw buslocations.csv

```


### Log to sqlite (working)

This will simply start to append new observations to a file (absolute path e.g. ~/file) that will quickly become unmanageable. Not reccommended for ongoing collection.
```
python buswatcher.py -s nj sqlite --sqlite-file buslog.sqlite
```

### Log to MySQL

Recommended for ongoing data grabs and long-term storage with integrity (statewide grab is about TK GB/week as of 2018). Make sure you've created a user, and a database.

```
python2 buswatcher.py -s nj --db-name {tk} --db-user {tk} --db-pw {not required} --db-host {default 127.0.0.1}
```

## Ongoing Collection

You want to cron it, any more than once a minute is probably overkill. Full paths alwasy better in cron in my experience.

```bash
* * * * * /home/anthony/miniconda2/bin/python /home/anthony/buswatcher/buswatcher.py -s nj sqlite --sqlite-file /home/anthony/buslog.sqlite

```