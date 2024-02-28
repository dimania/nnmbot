
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
    cursor.execute("DELETE FROM Users WHERE id_user = ?", (id_user.))
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
    else            
        cursor.execute("SELECT active,rights,name_user FROM Users")
             
    rows = cursor.fetchall()
    return rows

def db_list_tagged_films( id_user=None, tag=1 ):
    ''' List only records with set tag '''
    cursor.execute("SELECT name,nnm_url FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
    rows = cursor.fetchall()
    return rows

def db_clear_download( download ): #FIXME Not use in future
    ''' Set to N records with set tag download to 1 '''
    cursor.execute("UPDATE Films SET download=? WHERE download = 1", (download,))
    connection.commit()
    return str(cursor.rowcount)

def db_add_tag( id_nnm, tag, id_user )
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






