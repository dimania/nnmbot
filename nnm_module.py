#
#
# Database function
#
#
import os.path
    
def db_init():
    ''' Initialize database '''
    # Load ICU extension in exist for case independet search  in DB
    if os.path.isfile(ICU_extension_lib):
        connection.enable_load_extension(True)
        connection.load_extension(ICU_extension_lib)

    cursor.execute('''PRAGMA foreign_keys = ON''')

    # Create basic table Films
    cursor.execute('''
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
      ''')
    # Ctreate table Users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Users (
      id_user TEXT NOT NULL PRIMARY KEY,
      name_user TEXT NOT NULL,
      date TEXT NOT NULL,
      active INTEGER DEFAULT 0,
      rights INTEGER DEFAULT 0
      )
      ''')
    # Create table Ufilms - films tagged users
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS Ufilms (
      ufilms_id INTEGER PRIMARY KEY AUTOINCREMENT,
      id_user TEXT NOT NULL,
      id_FILMS  TEXT NOT NULL,
      date  TEXT NOT NULL,
      download INTEGER DEFAULT 0,
      FOREIGN KEY (id_user)
      REFERENCES Users (id_user)
        ON DELETE CASCADE
       )
      ''')

    connection.commit()

def db_add_film(id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb):
    ''' Add new Film to database '''
    cur_date = datetime.now()
    cursor.execute("INSERT INTO Films (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, date) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   (id_msg, id_nnm, nnm_url, name, id_kpsk, id_imdb, cur_date))
    connection.commit()

def db_exist_Id(id_kpsk, id_imdb):
    ''' Test exist Film in database '''
    cursor.execute(
        "SELECT 1 FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk, id_imdb))
    return cursor.fetchone()

def db_get_id_nnm(id_msg):
    ''' Get id_nm by id_msg '''
    cursor.execute("SELECT id_nnm FROM Films WHERE id_msg = ?", (id_msg,))
    row = cursor.fetchone()
    if row:
        return dict(row).get('id_nnm')
    else:
        return None

def db_info():
    ''' Get Info database: all records, tagged for download records and tagged early records '''
    cursor.execute(
        "SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Films WHERE download = 1 UNION ALL SELECT COUNT(*) FROM Films WHERE download = 2")
    rows = cursor.fetchall()
    return rows

def db_switch_download(id_nnm, download):
    ''' Set tag in database for download film late '''
    cursor.execute("UPDATE Films SET download=? WHERE id_nnm=?",
                   (download, id_nnm))
    connection.commit()
    return str(cursor.rowcount)

def db_list_all():
    ''' List all database '''
    cursor.execute('SELECT  * FROM Films')
    rows = cursor.fetchall()
    return rows

def db_list_download(download):
    ''' List only records with set tag download '''
    cursor.execute(
        "SELECT name,nnm_url FROM Films WHERE download = ?", (download,))
    rows = cursor.fetchall()
    # for row in rows:
    #  print(dict(row))
    return rows

def db_search(str_search):
    ''' Search in db '''
    str_search = '%'+str_search+'%'
    cursor.execute(
        "SELECT name,nnm_url FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
    rows = cursor.fetchall()
    return rows

def db_clear_download(download):
    ''' Set to N records with set tag download to 1 '''
    cursor.execute(
        "UPDATE Films SET download=? WHERE download = 1", (download,))
    connection.commit()
    return str(cursor.rowcount)

def db_add_user( id_user, name_user ):
    ''' Add new user to database '''
    cur_date=datetime.now()
    try:
      cursor.execute("INSERT INTO Users (id_user, name_user, date) VALUES(?, ?, ?)",\
      (id_user, name_user, cur_date,))
      connection.commit()
    except Exception as IntegrityError:
      logging.error(f"User already exist in BD\n") 
      logging.error(f"Original Error is: {IntegrityError}")           
      return 1
   
    return 0

def db_del_user( id_user ):
    '''Delete user from database and user tagged films'''
    cursor.execute("DELETE FROM Users WHERE id_user = ?", (id_user,))
    rows = cursor.fetchall()
    return rows

def db_exist_user( id_user ):
    ''' Test exist User in database '''
    cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ?", (id_user,))
    rows = cursor.fetchall()
    return rows

def db_ch_rights_user( id_user, active, rights ):
    ''' Change rights and status (active or blocked) for user '''
    cursor.execute("UPDATE Users SET (active=?,rights=?) WHERE id_user = ?", (active,rights,id_user,))
    connection.commit()
    return str(cursor.rowcount)  

def db_list_users( id_user=None, active=None, rights=None ):
    '''List users in database '''
    if id_user and active and rights:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ? AND active = ? AND rights = ?", (id_user, active, rights,))
    elif id_user and active:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ? AND active = ?", (id_user, active,))
    elif id_user and rights:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ? AND rights = ?", (id_user, rights,))    
    elif active and rights:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE active = ? AND rights = ?", (active, rights,))        
    elif id_user:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ?", (id_user,))
    elif active:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE active = ?", (active,))
    elif rights:
        cursor.execute("SELECT active,rights,name_user FROM Users WHERE rights = ?", (rights,))
    else:            
        cursor.execute("SELECT active,rights,name_user FROM Users")
             
    rows = cursor.fetchall()
    return rows

def db_list_tagged_films( id_user=None, tag=1 ):
    ''' List only records with set tag '''
    cursor.execute("SELECT name,nnm_url FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = cursor.fetchall()
    return rows

def db_add_tag( id_nnm, tag, id_user ):
    ''' User first Tag film in database '''
    cur_date=datetime.now()
    cursor.execute("INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (?,(SELECT id FROM Films WHERE id_nnm=?),?,?)",
                  (id_user,id_nnm,cur_date,tag))
    
    connection.commit()
    return str(cursor.rowcount)

def db_switch_tag( id_nnm, tag, id_user ):
    ''' Update tag in database for control film '''
    cursor.execute("UPDATE Ufilms SET tag=? WHERE id_user = ? AND id_Films = (SELECT id FROM Films WHERE id_nnm=?)",
                  (tag,id_user,id_nnm))
    connection.commit()
    return str(cursor.rowcount)
    
def db_get_tag( id_nnm, id_user ):
    ''' Get if exist current tag for user '''
    cursor.execute("SELECT tag FROM Ufilms WHERE id_Films = (SELECT id FROM Films WHERE id_nnm=?) AND id_user=?", (id_nnm, id_user,))
    rows = cursor.fetchall()
    return rows






