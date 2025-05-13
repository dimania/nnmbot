# Telegram Bot for filter films from NNMCLUB channel
# version 0.5
# Module dbmodule_nnmbot.py use aiosqlite Dbatabase functions  
#
#


from datetime import datetime
import logging
import os.path
import asyncio
import aiosqlite
import sqlite3

import settings as sts

class DatabaseBot:

    def __init__(self, db_file):
        self.db_file = db_file
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        self.dbm = await aiosqlite.connect(self.db_file)
        await self.dbm.execute("PRAGMA foreign_keys = ON")
        await self.dbm.commit()

        if sts.ICU_extension_lib and os.path.isfile(sts.ICU_extension_lib):
            await self.dbm.enable_load_extension(True)
            await self.dbm.load_extension(sts.ICU_extension_lib)

        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.dbm.close()

   
    async def db_create( self ):
        ''' Creta DB if not exist '''

        # Create basic table Films
        await self.dbm.execute('''PRAGMA journal_mode=WAL''')  # Активация WAL

        await self.dbm.execute('''
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
        await self.dbm.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        id_user TEXT NOT NULL PRIMARY KEY,
        name_user TEXT NOT NULL,
        date TEXT NOT NULL,
        active INTEGER DEFAULT 0,
        rights INTEGER DEFAULT 0,
        setings TEXT DEFAULT NULL
        )
        ''')
        # Create table Ufilms - films tagged users
        await self.dbm.execute('''
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

        await self.dbm.commit()

        return None

    async def db_modify(self, *args):
        ''' Update or insert data in db - common function'''

        global FAIL_MODIFY #  for test raice condition - remove in prod
        for i in range(sts.RETRIES_DB_LOCK):
            try:
                async with self.lock:
                    async with self.dbm.execute(args[0],args[1]) as cursor:
                        await self.dbm.commit()
                        logging.debug(f"SQL MODIFY: result={str(cursor.rowcount)}" )
                        return cursor
            except aiosqlite.OperationalError as error:        
                await asyncio.sleep(0.1)  
                logging.info(f"Retry add in db:{i} Error:{error}")
                FAIL_MODIFY = FAIL_MODIFY + 1  #  for test raice condition - remove in prod 
            except aiosqlite.IntegrityError as error:               
                logging.error(f"DB Modify Error is: {error}")
                #FIXME 
                return -1            
        else: 
            logging.error(f"Error INSERT data in DB! Retries pass:{i}")
            return None           
            
    async def db_add_film(self, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 ):
        ''' Add new Film to database '''
        cur_date = datetime.now()

        cursor = await self.db_modify("INSERT INTO Films (id_nnm, nnm_url, name, id_kpsk, id_imdb, \
                              mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url, image_nnm, \
                              publish, date) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )",
                                (id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                                    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url,\
                                        image_nnm, publish, cur_date ))
        if cursor: 
            return str(cursor.lastrowid)
        else:
            return None
                        
    async def db_update_film(self, idf, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 2 ):
        ''' Update Film in database '''
        cur_date = datetime.now()
      
        cursor = await self.db_modify("UPDATE Films SET id_nnm=?, nnm_url=?, name=?, id_kpsk=?, id_imdb=?, \
                        mag_link=?, section=?, genre=?, rating_kpsk=?, rating_imdb=?, \
                            description=?, image_nnm_url=?, image_nnm=?, publish=?, date=? WHERE id = ?", \
                            (id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, \
                                film_section, film_genre, film_rating_kpsk, film_rating_imdb, \
                                    film_description, image_nnm_url, image_nnm, publish, cur_date, idf ))
        if cursor:              
            logging.debug(f"SQL UPDATE FILM: id={idf} result={str(cursor.rowcount)}" )
            return str(cursor.rowcount)
        else:
            return None

    async def db_exist_Id(self, id_kpsk, id_imdb):
        ''' Test exist Film in database '''
        if id_kpsk == 0: 
            cursor = await self.dbm.execute("SELECT id FROM Films WHERE id_imdb = ?", (id_imdb,))
        elif id_imdb == 0:
            cursor = await self.dbm.execute("SELECT id FROM Films WHERE id_kpsk = ?", (id_kpsk,))
        else:
            cursor = await self.dbm.execute("SELECT id FROM Films WHERE id_kpsk = ? OR id_imdb = ?", (id_kpsk, id_imdb))
        
        return await cursor.fetchone()

    async def db_info( self, id_user ):
        ''' Get Info database: all records, tagged records and tagged early records for user '''
        cursor = await self.dbm.execute("SELECT COUNT(*) FROM Films UNION ALL SELECT COUNT(*) FROM Ufilms \
            WHERE tag = ? AND id_user = ? UNION ALL SELECT COUNT(*) FROM Ufilms \
                WHERE tag = ? AND id_user = ?", (sts.SETTAG, id_user, sts.UNSETTAG, id_user,) )
        
        return await cursor.fetchall()

    async def db_list_4_publish(self):
        ''' List records for publish on Channel form database '''
    
        cursor = await self.dbm.execute("SELECT id FROM Films WHERE publish = ? OR publish = ?", (sts.PUBL_NOT, sts.PUBL_UPD) )
        return await cursor.fetchall()

    async def db_update_publish(self, idf ):
        ''' Update record to PUBL_YES when publish on Channel  '''
        
        cursor = await self.db_modify("UPDATE Films SET publish = ? WHERE id = ?", (sts.PUBL_YES, idf,))
        if cursor:                          
            return str(cursor.rowcount)
        else:
            return None
        
    async def db_list_all(self):
        ''' List all records form database '''
        cursor = await self.dbm.execute("SELECT name, nnm_url, mag_link FROM Films")
        return  await cursor.fetchall()

    async def db_list_all_id(self):
        ''' List only id all records from database '''
        cursor = await self.dbm.execute("SELECT id FROM Films")
        return await cursor.fetchall()

    async def db_search_list(self, str_search):
        ''' Search in db '''
        str_search = '%'+str_search+'%'
        cursor = await self.dbm.execute(
            "SELECT name, nnm_url, mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url FROM Films \
                WHERE name LIKE ? COLLATE NOCASE", (str_search,))
        return await cursor.fetchall()

    async def db_search_id(self, str_search):
        ''' Search in db '''
        str_search = '%'+str_search+'%'
        cursor = await self.dbm.execute(
            "SELECT id FROM Films WHERE name LIKE ? COLLATE NOCASE", (str_search,))
        return await cursor.fetchall()

    async def db_add_user(self, id_user, name_user):
        ''' Add new user to database '''
        cur_date=datetime.now()
        #FIXME neet another analize return values
        cursor = await self.db_modify("INSERT INTO Users (id_user, name_user, date) VALUES(?, ?, ?)",\
            (id_user, name_user, cur_date,))
        if cursor == -1:           
            logging.error("User already exist in BD\n")
            logging.error(f"Original Error is: {error}")
            return 1
        if cursor == None: 
            logging.error(f"Error INSERT data in DB! pass {i}")
            return None
        return 0           


    async def db_del_user(self, id_user):
        '''Delete user from database and user tagged films'''
        cursor = await self.dbm.execute("DELETE FROM Users WHERE id_user = ?", (id_user,))
        await self.dbm.commit()
        return await cursor.fetchall()

    async def db_exist_user(self, id_user):
        ''' Test exist User in database '''
        cursor = await self.dbm.execute("SELECT active,rights,name_user FROM Users WHERE id_user = ?", (id_user,))
        return await cursor.fetchall()
        
    async def db_ch_rights_user(self, id_user, active, rights):
        ''' Change rights and status (active or blocked) for user '''
        
        cursor = await self.db_modify("UPDATE Users SET active=?, rights=? WHERE id_user = ?", (active,rights,id_user))
        if cursor:    
            logging.info(f"SQL UPDATE: id_user={id_user} active={active}, rights={rights} result={str(cursor.rowcount)}" )                      
            return str(cursor.rowcount)
        else:
            return None
        
        
        
    async def db_list_users(self, id_user=None, active=None, rights=None ):
        '''List users in database '''
        
        if id_user is not None and active is not None and rights is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ? AND rights = ?", (id_user, active, rights,))
        elif id_user is not None and active is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND active = ?", (id_user, active,))
        elif id_user is not None and rights is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ? AND rights = ?", (id_user, rights,))
        elif active is not None and rights is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ? AND rights = ?", (active, rights,))
        elif id_user is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE id_user = ?", (id_user,))
        elif active is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE active = ?", (active,))
        elif rights is not None:
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users WHERE rights = ?", (rights,))
        else:            
            cursor = await self.dbm.execute("SELECT active,rights,name_user,id_user,date FROM Users")

        rows = await cursor.fetchall()
        logging.debug(f"SELECT USERS: id_user={id_user} active={active}, rights={rights} result={len(rows)}" )        
        return rows
        
    async def db_list_tagged_films(self,  id_user=None, tag=sts.SETTAG):
        ''' List only records with set tag '''
        cursor = await self.dbm.execute("SELECT name,nnm_url,mag_link FROM Films WHERE id IN (SELECT id_Films FROM Ufilms \
            WHERE id_user=? and tag=?)", (id_user,tag,))
        return await cursor.fetchall()

    async def db_list_tagged_films_id(self, id_user=None, tag=sts.SETTAG):
        ''' List only records with set tag '''
        cursor = await self.dbm.execute("SELECT id FROM Films WHERE id IN (SELECT id_Films FROM Ufilms WHERE id_user=? and tag=?)", (id_user,tag,))
        return await cursor.fetchall()

    async def db_film_by_id(self, id=None):
        ''' List info by id record '''
        cursor = await self.dbm.execute("SELECT name, nnm_url, mag_link, section, genre, rating_kpsk, rating_imdb, description, image_nnm_url,\
                            image_nnm, publish, id_nnm FROM Films WHERE id=?", (id,))
        return await cursor.fetchone()

    async def db_add_tag(self, id_nnm, tag, id_user):
        ''' User first Tag film in database '''
        cur_date=datetime.now()        
        cursor = await self.db_modify("INSERT INTO Ufilms (id_user, id_Films, date, tag) VALUES (?,(SELECT id FROM Films WHERE id_nnm=?),?,?)",
                    (id_user,id_nnm,cur_date,tag))
        if cursor:                                    
            return str(cursor.rowcount)
        else:
            return None

    async def db_switch_film_tag(self, id_nnm, tag, id_user):
        ''' Update user tagging in database for films  '''
        
        cursor = await self.db_modify("UPDATE Ufilms SET tag=? WHERE id_user = ? AND id_Films = (SELECT id FROM Films WHERE id_nnm=?)",
                    (tag,id_user,id_nnm)) 
        if cursor:                                    
            return str(cursor.rowcount)
        else:
            return None

    async def db_switch_user_tag(self, id_user, tag):
        ''' Update tag in database for user '''
        
        cursor = await self.db_modify("UPDATE Ufilms SET tag=? WHERE id_user = ?", (tag,id_user))
        if cursor:                                    
            return str(cursor.rowcount)
        else:
            return None               

    async def db_get_tag(self, id_nnm, id_user ):
        ''' Get if exist current tag for user '''
        cursor = await self.dbm.execute("SELECT tag FROM Ufilms WHERE id_Films = (SELECT id FROM Films WHERE id_nnm=?) AND id_user=?", (id_nnm, id_user,))
        return await cursor.fetchall()


# For test block task
async def test_db_add(id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                        film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0):
    ''' Test dblock'''
   
    async with DatabaseBot(sts.db_name) as db:    
            rec_id = await db.db_add_film(id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                        film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 )
    print(f'rec_id={rec_id}')
             
        
async def test_db_update(idf, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 2 ):
    '''Test dblock update db'''
   
    async with DatabaseBot(sts.db_name) as db:    
        rec_id = await db.db_update_film(idf, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 )
    print(f'rec_id={rec_id}')
      
async def test_db_list_all():
    '''Test dblock list all rec'''
    async with DatabaseBot(sts.db_name) as db:   
            rec_id = await db.db_list_all_id()
    #print(f'rec_id={rec_id}')
    print(f'------------------------------rec_id={len(rec_id)}-------------------------------------')
        

FAIL_MODIFY=0

async def main():
    """
    This is the main entry point for the program
    """
    print("Begin main")
    
    sts.get_config()
    sts.logfile = 'db_module_aio.log'
    sts.db_name='test_aio_db.db'

   # Enable logging
    logging.basicConfig(level=sts.log_level, filename="backend_"+sts.logfile, filemode="a", format="%(asctime)s %(levelname)s %(message)s")
    logging.info("--------------------------------------\nStart db_module_aio.")

    
      
    id_nnm='12345'
    nnm_url='http://test.ru'
    name='Test film'
    id_kpsk='kp12345'
    id_imdb='imdb12345'
    film_magnet_link=None
    film_section='Test Section'
    film_genre='Genre'
    film_rating_kpsk='5'
    film_rating_imdb='8'
    film_description='Description test'
    image_nnm_url='http://test_image.ru'
    image_nnm=None
    #---
    id_user='12345678'
    name_user='test_user'
    active=1
    rights=0
    publish=0
    cur_date=datetime.now()



    async with DatabaseBot(sts.db_name) as db:
        await db.db_create()

    async with DatabaseBot(sts.db_name) as db:    
        rec_id = await db.db_add_film(id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 )
    print(f'rec_id={rec_id}')
   
    async with DatabaseBot(sts.db_name) as db:    
        rec_id = await db.db_update_film(rec_id, id_nnm, nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                    film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0 )
    print(f'rec_id={rec_id}')
    
    # Test race condition 
    count=10
    tasks=[]
    for i in range(1, count+1):
        # создаем задачи
        task = test_db_add(id_nnm+str(i), nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                        film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0)
        # складываем задачи в список
        tasks.append(task)
        
        task=test_db_list_all()

        # складываем задачи в список
        tasks.append(task)
        
        # создаем задачи
        task = test_db_update(i,id_nnm+str(i), nnm_url, name, id_kpsk, id_imdb, film_magnet_link, film_section, \
                        film_genre, film_rating_kpsk, film_rating_imdb, film_description, image_nnm_url, image_nnm, publish = 0)
        # складываем задачи в список
        tasks.append(task)
        
    # планируем одновременные вызовы
    await asyncio.gather(*tasks)
    
    print(f'--------------INFO--------------')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_info( id_user )
    print(f'rec_id={rec_id}')

    print(f'--------------INFO--------------')

    print(f'FAIL_MODIFY={FAIL_MODIFY} ')

    
    #exit()

    async with DatabaseBot(sts.db_name) as db:    
        rec_id = await db.db_exist_Id(id_kpsk, id_imdb)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_info( id_user )
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_4_publish()
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_update_publish( 1 )
    print(f'rec_id={rec_id}')
        
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_all()
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_all_id()
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_search_list('test')
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_search_id('test')
    print(f'rec_id={rec_id}')   

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_add_user( id_user, name_user )
    print(f'rec_id={rec_id}')
    
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_del_user( id_user )
    print(f'rec_id={rec_id}')
    # Yet one for test
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_add_user( id_user, name_user )
    print(f'rec_id={rec_id}')
     # Yet one for test exception
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_add_user( id_user, name_user )
    print(f'rec_id={rec_id}')
    #exit()
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_exist_user(id_user)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_ch_rights_user(id_user, active, rights)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_users( id_user, active, rights )
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_tagged_films( id_user, tag=sts.SETTAG )
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_list_tagged_films_id( id_user, tag=sts.SETTAG )
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_film_by_id(id=1)
    print(f'rec_id={rec_id}')


    print(f"Add tag failed:id_nnm:{id_nnm},tag:{sts.SETTAG}, id_user:{id_user}")
    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_add_tag(id_nnm, sts.SETTAG, id_user)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_switch_film_tag(id_nnm, sts.SETTAG, id_user)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_switch_user_tag(id_user, sts.SETTAG)
    print(f'rec_id={rec_id}')

    async with DatabaseBot(sts.db_name) as db:   
        rec_id = await db.db_get_tag( id_nnm, id_user )
    print(f'rec_id={rec_id}')

if __name__ == "__main__":
    asyncio.run(main())
