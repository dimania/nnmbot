#!/bin/sh
#
# migrate database from old version
#
# Use migrate_db.sh olddatabase.db newdatabase.db
#
#
#|| [ "$2" == "" ]

OLD_DB=$1
NEW_DB=$2

if [ "$OLD_DB" == "" ]; then
 echo "No parameters!"
 echo "Use migrate_db.sh olddatabase.db newdatabase.db"
 echo "Use migrate_db.sh olddatabase.db"
 echo "In second case new db will be created as newdatabase.bd"
 exit 0
fi

if [ "$NEW_DB" == "" ]; then

sqlite3  newdatabase.db <<EOF
      PRAGMA foreign_keys = ON;

      CREATE TABLE IF NOT EXISTS Films (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_msg TEXT,
      id_nnm TEXT,
      nnm_url TEXT,
      name TEXT,
      id_kpsk TEXT,
      id_imdb TEXT,
      date TEXT
      );

      CREATE TABLE IF NOT EXISTS Users (
      id_user TEXT NOT NULL PRIMARY KEY,
      name_user TEXT NOT NULL,
      date TEXT NOT NULL,
      active INTEGER DEFAULT 0,
      rights INTEGER DEFAULT 0
      );

      CREATE TABLE IF NOT EXISTS Ufilms (
      ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_user TEXT NOT NULL,
      id_Films  TEXT NOT NULL,
      date  TEXT NOT NULL,
      tag INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       );
EOF

NEW_DB=newdatabase.db
fi


sqlite3 <<EOF_2
ATTACH "$OLD_DB" AS old;
ATTACH "$NEW_DB" AS new;
.databases
INSERT INTO new.Films(id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date) SELECT id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date FROM old.Films;
EOF_2

exit 0

# new shema
      CREATE TABLE IF NOT EXISTS Films (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_msg TEXT,
      id_nnm TEXT,
      nnm_url TEXT,
      name TEXT,
      id_kpsk TEXT,
      id_imdb TEXT,
      date TEXT
      )
 # old shema
    CREATE TABLE IF NOT EXISTS Films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_msg TEXT,
    id_nnm TEXT,
    nnm_url TEXT,
    name TEXT,
    id_kpsk TEXT,
    id_imdb TEXT,
    date TEXT,
    download INT DEFAULT 0
    )
