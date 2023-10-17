#!/bin/sh

sqlite3 ./var/enrollmentDatabase.db < ./share/enrollmentDatabase.sql
sqlite3 ./var/authDatabase.db < ./share/authDatabase.sql
