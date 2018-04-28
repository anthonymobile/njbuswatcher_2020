# bus report card

Python wrapper to query XML based realtime bus locations.  Currently supports NJ.

Some notebooks have been added as examples.


## Usage
It's worth checking to make sure your pipeline is working before trying to automate the data collection. Otherwise you are asking for a lot of nasty emails from your cron daemon.

### Testing
```
python2 buswatcher.py -s nj --save-raw buslocations.csv

```


### Logging to sqlite

This will simply start to append new observations to a file (absolute path e.g. ~/file) that will quickly become unmanageable. Not recommended for ongoing collection.
```
python buswatcher.py -s nj sqlite --sqlite-file buslog.sqlite
```

### Logging to MySQL

Recommended for ongoing data grabs and long-term storage with integrity (statewide grab is about TK GB/week as of 2018). Make sure you've created a user, and a database.

```
python2 buswatcher.py -s nj --db-name {tk} --db-user {tk} --db-pw {not required} --db-host {default 127.0.0.1}
```

### Logging to mongodb

TBD. Would love to add if someone wants to rewrite or extend one of the current classes. Not sure if or when this would start to become necessary given size and use of the log.

## Ongoing Collection

You want to cron it, any more than once a minute is probably overkill - though there are a couple of urban design use cases we've envisioned where finer-grained movements might be useful. Full paths always better in cron in my experience.

```bash
* * * * * /home/anthony/miniconda2/bin/python /home/anthony/buswatcher/buswatcher.py -s nj mysql --db-name bus_position_log --db-user buswatcher --db-pw njtransit
```

For New Jersey, this will tuck in at around 100-150 GB a year in SQLite, snapping once a minute. YMMV with higher frequency or different databases. Currently, we have this setup on a Digital Ocean ubuntu 16 droplet, pushign the data to a MYsql database vault stored on Amazon S3 via a FUSE mount. Here are how-tos on [moving your database directory](https://www.digitalocean.com/community/tutorials/how-to-move-a-mysql-data-directory-to-a-new-location-on-ubuntu-16-04) and [connecting Ubuntu and S3](https://firefli.de/tutorials/s3fs-and-aws.html). 