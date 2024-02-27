
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_msg TEXT  NOT NULL,
    id_nnm TEXT  NOT NULL,
    nnm_url TEXT  NOT NULL,
    name TEXT  NOT NULL,
    id_kpsk TEXT,
    id_imdb TEXT,
    date TEXT  NOT NULL,
    download INTEGER DEFAULT 0
    );

DROP TABLE Users;    

users_id INTEGER AUTOINCREMENT,

CREATE TABLE IF NOT EXISTS Users (    
    id_user TEXT NOT NULL PRIMARY KEY,
    name_user TEXT NOT NULL,
    date TEXT NOT NULL,
    active INTEGER DEFAULT 0,
    rights INTEGER DEFAULT 0
);

DROP TABLE Ufilms;
CREATE TABLE IF NOT EXISTS Ufilms (
    ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user TEXT NOT NULL,
    id_FILMS  TEXT NOT NULL,
    date  TEXT NOT NULL,
    download INTEGER DEFAULT 0,
    FOREIGN KEY (id_user)
    REFERENCES Users (id_user)
      ON DELETE CASCADE
);




INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('12345','dima', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('56789','kat', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('101112','denis', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('1213141516','alla', '26.02.2024',0,0);

INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('12345',10,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('12345',11,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('12345',12,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('12345',13,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('12345',14,'26.02.2024');

INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('56789',10,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('56789',11,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('56789',12,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('56789',13,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES ('56789',14,'26.02.2024');

INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (101112,10,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (101112,11,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (101112,12,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (101112,13,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (101112,14,'26.02.2024');

INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (1213141516,10,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (1213141516,11,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (1213141516,12,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (1213141516,13,'26.02.2024');
INSERT INTO Ufilms (id_user, id_FILMS, date) VALUES (1213141516,14,'26.02.2024');

SELECT * FROM Ufilms;
SELECT * FROM Users;

DELETE FROM Users WHERE id_user = '12345';

first_name='Дмитрий


SELECT active,rights,name_user FROM Users WHERE id_user = 1033339697;


