#!/bin/sh

sqlite3 ./var/primary/fuse/enrollmentDatabase.db < ./share/enrollmentDatabase.sql
sqlite3 ./var/primary/fuse/authDatabase.db < ./share/authDatabase.sql
