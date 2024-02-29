
PRAGMA foreign_keys = ON;

DROP TABLE Films;

CREATE TABLE IF NOT EXISTS Films (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_msg TEXT  NOT NULL,
    id_nnm TEXT  NOT NULL,
    nnm_url TEXT  NOT NULL,
    name TEXT  NOT NULL,
    id_kpsk TEXT,
    id_imdb TEXT,
    date TEXT  NOT NULL,
    tag INTEGER DEFAULT 0
    );

DROP TABLE Users;    

--users_id INTEGER AUTOINCREMENT,

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
    id_Films  TEXT NOT NULL,
    date  TEXT NOT NULL,
    tag INTEGER DEFAULT 0,
    FOREIGN KEY (id_user)
    REFERENCES Users (id_user)
      ON DELETE CASCADE
);



INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date ) VALUES ('123','a1','http://url/1','Film1','12345','54321','26.02.2024');
INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date ) VALUES ('123','a2','http://url/2','Film2','12345','54321','26.02.2024');
INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date ) VALUES ('123','a3','http://url/3','Film3','12345','54321','26.02.2024');
INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date ) VALUES ('123','a4','http://url/4','Film4','12345','54321','26.02.2024');
INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date ) VALUES ('123','a5','http://url/5','Film5','12345','54321','26.02.2024');



INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('12345','dima', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('56789','kat', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('101112','denis', '26.02.2024',0,0);
INSERT INTO Users (id_user, name_user, date, active, rights) VALUES ('1213141516','alla', '26.02.2024',0,0);

INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',5,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',1,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',2,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',3,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',4,'26.02.2024',1);

INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('56789',5,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('56789',1,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('56789',2,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('56789',3,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('56789',4,'26.02.2024',1);

INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (101112,5,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (101112,1,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (101112,2,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (101112,3,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (101112,4,'26.02.2024',1);

INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (1213141516,5,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (1213141516,1,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (1213141516,2,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (1213141516,3,'26.02.2024',1);
INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (1213141516,4,'26.02.2024',1);

--SELECT * FROM Ufilms;
--SELECT * FROM Users;
--SELECT * FROM Films;
--DELETE FROM Users WHERE id_user = '12345';
--SELECT active,rights,name_user FROM Users WHERE id_user = 1033339697;
--SELECT name,nnm_url FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=12345 and tag=1);
--SELECT id_Films FROM Ufilms WHERE id_user=12345 and tag=1;

-- switch( id_user, id_nnm, tag )
--UPDATE Ufilms SET tag=2, id_Films = (SELECT id FROM Films WHERE id_nnm='a5') WHERE id_user = 12345 AND ;  
--UPDATE Ufilms SET tag=2 WHERE id_user = 12345 AND id_Films = (SELECT id FROM Films WHERE id_nnm='a5'); 
--INSERT INTO Ufilms  tag=2, id_Films = (SELECT id FROM Films WHERE id_nnm='a5') WHERE id_user = 12345; 

--INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES ('12345',(SELECT id FROM Films WHERE id_nnm='a5'),'26.02.2024',1);

--SELECT id FROM Films WHERE id_nnm = 'a5';

SELECT tag FROM Ufilms WHERE id_Films = (SELECT id FROM Films WHERE id_nnm='as5') AND id_user=12345;
SELECT active,rights,name_user,id_user FROM Users WHERE active = 0;
