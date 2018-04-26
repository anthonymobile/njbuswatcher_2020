# bus report card

Python wrapper to query XML based realtime bus locations.  Currently supports NJ.

Some notebooks have been added as examples.


## Usage


### Testing
```
python2 buswatcher.py -s nj --save-raw buslocations.csv

```


### Log to sqlite

This will simply start to append new observations to a file (absolute path e.g. ~/file) that will quickly become unmanageable. Not reccommended for ongoing collection.
```
python2 buswatcher.py -s nj sqlite --sqlite-file buslog.sqlite
```

### Log to MySQL

Recommended for ongoing data grabs and long-term storage with integrity (statewide grab is about TK GB/week as of 2018). Make sure you've created a user, and a database.

```
python2 buswatcher.py -s nj --db-name {tk} --db-user {tk} --db-pw {not required} --db-host {default 127.0.0.1}
```
