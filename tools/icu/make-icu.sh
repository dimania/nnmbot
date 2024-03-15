#!/bin/sh
#In debian 10 not exist libsqliteicu.so library
#I found instruction as compile this library on
#https://medium.com/@eigenein/%D1%80%D0%B5%D0%B3%D0%B8%D1%81%D1%82%D1%80%D0%BE%D0%BD%D0%B5%D0%B7%D0%B0%D0%B2%D0%B8%D1%81%D0%B8%D0%BC%D1%8B%D0%B9-like-%D0%B2-sqlite-%D0%B4%D0%BB%D1%8F-%D0%BA%D0%B8%D1%80%D0%B8%D0%BB%D0%BB%D0%B8%D1%86%D1%8B-95e3e33e8ad
#
#I correct compile coommand
#
#After compile copy  libsqliteicu.so to dir where nnmbot.py and correct you config.py

wget "https://www.sqlite.org/src/raw/ext/icu/icu.c?name=b2732aef0b076e4276d9b39b5a33cec7a05e1413" -O icu.c

mv icu.c icu.c.orig

sed 's/sqlite3_icu_init/sqlite3_sqliteicu_init/' ./icu.c.orig >icu.c

gcc -shared icu.c -g -o libsqliteicu.so -fPIC `pkg-config --libs --cflags icu-uc icu-io`

