# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module dbmodule_nnmbot.py  Dbatabase functions  
#
#


from datetime import datetime
import logging
import os.path
import json

import settings as sts

def db_init():
    ''' Initialize database '''
    # Load ICU extension in exist for case independet search  in DB
    if sts.ICU_extension_lib and os.path.isfile(sts.ICU_extension_lib):
        sts.connection.enable_load_extension(True)
        sts.connection.load_extension(sts.ICU_extension_lib)

    sts.cursor.execute('''PRAGMA foreign_keys = ON''')
    sts.connection.commit()

def db_create():
    ''' Creta DB if not exist '''

    # Create basic table Films
    # remove - id_msg TEXT,
    # remove: photo BLOB DEFAULT NULL,
    # add: publish INTEGER DEFAULT 0, - Flag no publish/upgrade/not publish - 1/2/0

    sts.cursor.execute('''
      CREATE TABLE IF NOT EXISTS Films (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_nnm TEXT,
      id_kpsk TEXT,
      id_imdb TEXT,
      nnm_url TEXT,
      name TEXT,
      mag_link TEXT DEFAULT NULL,
      section  TEXT DEFAULT NULL,
      genre  TEXT DEFAULT NULL,
      rating_kpsk TEXT DEFAULT NULL,
      rating_imdb TEXT DEFAULT NULL,
      description TEXT DEFAULT NULL,
      image_nnm_url TEXT NULL,
      image_nnm BLOB DEFAULT NULL,
      publish INTEGER DEFAULT 0,
      date TEXT
      )
      ''')
    # Ctreate table Users
    sts.cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
      id_user TEXT NOT NULL PRIMARY KEY,
      name_user TEXT NOT NULL,
      date TEXT NOT NULL,
      active INTEGER DEFAULT 0,
      rights INTEGER DEFAULT 0,
      setings TEXT DEFAULT NULL,
      share2users TEXT DEFAULT NULL, 
      users4share TEXT DEFAULT NULL                 
      )
      ''')
    # Create table Ufilms - films tagged users
    sts.cursor.execute('''
      CREATE TABLE IF NOT EXISTS Ufilms (
      ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_user TEXT NOT NULL,
      id_Films  TEXT NOT NULL,
      date  TEXT NOT NULL,
      tag INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       )
      ''')

    sts.connection.commit()

def db_add_film(id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 ):
    ''' Add new Film to database '''
    cur_date = datetime.now()
    sts.cursor.execute("INSERT INTO Films (id_nnm, nnm_url, name, id_kpsk, id_imdb, \
        mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url, image_nnm, publish, date) \
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )",
                   (id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish, cur_date ))
    sts.connection.commit()
    logging.debug(f"SQL INSERT FILM: id={id} result={str(sts.cursor.rowcount)}" )
    return str(sts.cursor.lastrowid)

def db_update_film(id, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 2 ):
    ''' Update Film in database '''
    cur_date = datetime.now()
    sts.cursor.execute("UPDATE Films SET id_nnm=?, nnm_url=?, name=?, id_kpsk=?, id_imdb=?, \
        mag_link=?, section=?, genre=?, rating_kpsk=?, rating_imdb=?, \
            description=?, image_nnm_url=?, image_nnm=?, publish=?, date=? WHERE id = ?", \
                (id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, \
                    film_section, film_genre, film_rating_kpsk, film_rating_imdb, \
                        film_description, image_nnm_url, image_nnm, publish, cur_date, id ))
    sts.connection.commit()
    logging.debug(f"SQL UPDATE FILM: id={id} result={str(sts.cursor.rowcount)}" )
    return str(sts.cursor.rowcount)

def db_exist_Id(id_kpsk, id_imdb):
    ''' Test exist Film in database '''
    if id_kpsk == 0: 
      sts.cursor.execute("SELECT id FROM Films WHERE id_imdb = ?", (id_imdb,))
    elif id_imdb == 0:
      sts.cursor.execute("SELECT id FROM Films WHERE id_kpsk = ?", (id_kpsk,))
    else:
      sts.cursor.execute("SELECT id FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk, id_imdb))
     
    return sts.cursor.fetchone()
    
def db_info( id_user ):
    ''' Get Info database: all records, tagged records and tagged early records for user '''
    sts.cursor.execute("SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Ufilms \
        WHERE tag = ? AND id_user = ? UNION ALL SELECT COUNT(*) FROM Ufilms \
            WHERE tag = ? AND id_user = ?", (sts.SETTAG, id_user, sts.UNSETTAG, id_user,) )
    rows = sts.cursor.fetchall()
    return rows

def db_list_4_publish():
    ''' List records for publish on Channel form database '''
   
    sts.cursor.execute("SELECT id FROM Films WHERE publish = ? OR publish = ?", (sts.PUBL_NOT, sts.PUBL_UPD) )
    rows = sts.cursor.fetchall()
    return rows

def db_update_publish( id ):
    ''' Update record to PUBL_YES when publish on Channel  '''
    sts.cursor.execute("UPDATE Films SET publish = ? WHERE id = ?", (sts.PUBL_YES, id,))
    sts.connection.commit()
    logging.debug(f"SQL UPDATE: id={id} publish={sts.PUBL_YES} result={str(sts.cursor.rowcount)}" )
    return str(sts.cursor.rowcount)  

def db_list_all():
    ''' List all records form database '''
    sts.cursor.execute("SELECT name, nnm_url, mag_link FROM Films")
    rows = sts.cursor.fetchall()
    return rows

def db_list_all_id():
    ''' List only id all records from database '''
    sts.cursor.execute("SELECT id FROM Films")
    rows = sts.cursor.fetchall()
    return rows

def db_search_old(str_search): #NO NEED LATE
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    sts.cursor.execute(
        "SELECT name, nnm_url, mag_link FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = sts.cursor.fetchall()
    return rows

def db_search_list(str_search):
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    sts.cursor.execute(
        "SELECT name, nnm_url, mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url FROM Films \
            WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = sts.cursor.fetchall()
    return rows

def db_search_id(str_search):
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    sts.cursor.execute(
        "SELECT id FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = sts.cursor.fetchall()
    return rows

def db_add_user( id_user, name_user ):
    ''' Add new user to database '''
    cur_date=datetime.now()
    try:
      sts.cursor.execute("INSERT INTO Users (id_user, name_user, date) VALUES(?, ?, ?)",\
      (id_user, name_user, cur_date,))
      sts.connection.commit()
    except Exception as IntegrityError:
      logging.error("User already exist in BD\n") 
      logging.error(f"Original Error is: {IntegrityError}")           
      return 1
   
    return 0

def db_del_user( id_user ):
    '''Delete user from database and user tagged films'''
    sts.cursor.execute("DELETE FROM Users WHERE id_user = ?", (id_user,))
    rows = sts.cursor.fetchall()
    return rows

def db_exist_user( id_user ):
    ''' Test exist User in database '''
    sts.cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ?", (id_user,))
    rows = sts.cursor.fetchall()
    return rows

def db_ch_rights_user( id_user, active, rights ):
    ''' Change rights and status (active or blocked) for user '''
    sts.cursor.execute("UPDATE Users SET active=?, rights=? WHERE id_user = ?", (active,rights,id_user))
    sts.connection.commit()
    logging.info(f"SQL UPDATE: id_user={id_user} active={active}, rights={rights} result={str(sts.cursor.rowcount)}" )
    return str(sts.cursor.rowcount)  

def db_list_users( id_user=None, active=None, rights=None ):
    '''List users in database '''
    
    if id_user is not None and active is not None and rights is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ? AND rights = ?", (id_user, active, rights,))
    elif id_user is not None and active is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ?", (id_user, active,))
    elif id_user is not None and rights is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND rights = ?", (id_user, rights,))
    elif active is not None and rights is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ? AND rights = ?", (active, rights,))
    elif id_user is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ?", (id_user,))
    elif active is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ?", (active,))
    elif rights is not None:
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE rights = ?", (rights,))
    else:            
        sts.cursor.execute("SELECT active,rights,name_user,id_user,date FROM Users")
             
    rows = sts.cursor.fetchall()
    
    logging.debug(f"SELECT USERS: id_user={id_user} active={active}, rights={rights} result={len(rows)}" )
    return rows

def db_list_tagged_films( id_user=None, tag=sts.SETTAG ):
    ''' List only records with set tag '''
    sts.cursor.execute("SELECT name,nnm_url,mag_link FROM Films WHERE id IN (SELECT id_Films FROM Ufilms \
        WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = sts.cursor.fetchall()
    return rows

def db_list_tagged_films_id( id_user=None, tag=sts.SETTAG ):
    ''' List only records with set tag '''
    sts.cursor.execute("SELECT id FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = sts.cursor.fetchall()
    return rows

def db_film_by_id( id=None ):
    ''' List info by id record '''
    sts.cursor.execute("SELECT name, nnm_url, mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url,\
                        image_nnm, publish, id_nnm FROM Films WHERE id=?", (id,))
    row = sts.cursor.fetchone()
    return row

def db_add_tag( id_nnm, tag, id_user ):
    ''' User first Tag film in database '''
    cur_date=datetime.now()
    sts.cursor.execute("INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (?,(SELECT id FROM Films WHERE id_nnm=?),?,?)",
                  (id_user,id_nnm,cur_date,tag))
    sts.connection.commit()
    return str(sts.cursor.rowcount)

def db_switch_film_tag( id_nnm, tag, id_user ):
    ''' Update user tagging in database for films  '''
    sts.cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ? AND id_Films = (SELECT id FROM Films WHERE id_nnm=?)",
                  (tag,id_user,id_nnm))
    sts.connection.commit()
    return str(sts.cursor.rowcount)

def db_switch_user_tag( id_user, tag ):
    ''' Update tag in database for user '''
    sts.cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ?", (tag,id_user))
    sts.connection.commit()
    return str(sts.cursor.rowcount)    
    
def db_get_tag( id_nnm, id_user ):
    ''' Get if exist current tag for user '''
    sts.cursor.execute("SELECT tag FROM Ufilms WHERE id_Films = (SELECT id FROM Films WHERE id_nnm=?) AND id_user=?", (id_nnm, id_user,))
    rows = sts.cursor.fetchall()
    return rows

def db_add_share( field, share2users, id_user ):
    ''' Add to user table users to whom share lists '''
    
    # From deepseeek
    try:
        # Получаем текущий JSON
        sts.cursor.execute(f"SELECT {field} FROM Users WHERE id_user = ?", (id_user,))
        result = sts.cursor.fetchone()
        
        # Десериализация или создание нового списка
        current_list = json.loads(result[0]) if result and result[0] else []
        
        # Добавляем новые элементы (поддерживает как одиночные, так и множественные значения)
        if isinstance(share2users, list):
            current_list.extend(share2users)
        else:
            current_list.append(share2users)
        
        # Обновляем запись в базе
        sts.cursor.execute( f"UPDATE Users SET {field} = ? WHERE id_user = ?",
            (json.dumps(current_list, ensure_ascii=False), id_user) )
        sts.connection.commit()
        
    except json.JSONDecodeError:
        logging.error(f"Error in format data: {share2users}\n")   
    finally:
        return True
        #sts.connection.close()

#def remove_from_list(db_path, record_id, value_to_remove, remove_all=False)
def db_del_share( field, users_to_remove, id_user ):
    '''Delete users from table to whom share lists '''

    try:
        # Получаем текущие данные
        #logging.error(f"Run del: {users_to_remove}/{field}/{id_user} \n")
        sts.cursor.execute(f"SELECT {field} FROM Users WHERE id_user = ?", (id_user,))
        result = sts.cursor.fetchone()
        logging.error(f"Result list: {result}\n")
        if not result or not result[0]:
            return False

        current_list = json.loads(result[0])
        #logging.error(f"Current list: {current_list}\n")

        new_list = [item for item in current_list if item != users_to_remove]
        #logging.error(f"New list: {new_list}\n")

        # Обновляем запись
        sts.cursor.execute( f"UPDATE Users SET {field} = ? WHERE id_user = ?",
            (json.dumps(new_list, ensure_ascii=False), id_user)
        )
        sts.connection.commit()
        return True

    except json.JSONDecodeError:
        logging.error(f"Error in format data: {users_to_remove}\n") 
        return False
    finally:
        return True

def db_get_share( field, id_user ):
    '''Get share users '''

    sts.cursor.execute(f"SELECT {field} FROM Users WHERE id_user = ?", (id_user,))
    result = sts.cursor.fetchone()
       
    if not result or not result[0]:
        return False

    current_list = json.loads(result[0])
    #logging.error(f"Current list: {current_list}\n")
    return current_list
    