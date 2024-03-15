# nnmbot                             
[English](#description)
## Описание
Telegram Bot для фильтрации Телеграм канала [NNMCLUB](t.me/nnmclubtor)  <br> <br>
Скрипрт на Python прослушивает Телеграм канал [NNMCLUB](t.me/nnmclubtor) и пересылает сообщения содержащие информацию только о фильмах на ваш личный канал. Фильтр настаривается в конфигурационном файле. <br><br>
Bot получает описание фильма с сайта https://nnmclub.to и рейтинг фильма с сайта [Кинопоиска](https://www.kinopoisk.ru) и [Imdb](https://www.imdb.com).<br><br>
Ведет локальную базу данных о пересланных сообщениях - фильмах.<br><br>
Исключает из пересылки повторяющиеся фильмы.<br><br>
На данный момент используется два подключения к Telegram. Одно подключение как пользователь, второе как Bot. Два подключения используется потому, что Bot не может прослушивать каналы на которые он не подписан. 

Для прослушивания используется первое подключение как пользователя. С помощью этого соединения получаем сообщения согласно настроенному фильтру, из канала [NNMCLUB](t.me/nnmclubtor) и пересылаем его в наш личный канал. Там сообщение подхватывает уже Bot - второе соединение и присоединяет к нему кнопки управления - 'Добавить' и 'Управлять'.

### Пользователи
Новые пользователи могут подать заявку на регистрацию, после рассмотрения заявки администратром им станет доступно:
1. По кнопке Добавить:
*  Добавлять (отмечать) фильмы в базу данных.
2. По кнопке Управлять:
* Просматривать список добавленных фильмов.
* Очищать список добавленных фильмов.
* Просматривать ранее добавленные и очищенные фильмы.
* Искать фильмы в базе данных.
* Получить информацию о базе данных.


### Администратор
Пользователи которые являются Администраторами канала автоматически являются и Администраторами бота.
Процедура регистрации администратора аналогична процедуре для пользоателя:
1. Подать заявку на подключение.
2. Вернуться в канал и еще раз нажать Управление.
3. В меню работы с пользователями одобрить запрос от себя.

Администраторам доступно:
1. По кнопке Добавить:
  * Добавлять (отмечать) фильмы в базе данных для последующей работы.
2. По кнопке Управлять:
  * Просматривать список добавленных фильмов.
  * Очищать список добавленных фильмов.
  * Просматривать ранее добавленные и очищенные фильмы.
  * Искать фильмы в базе данных.
  * Получить информацию о базе данных.
  * Получить список всех фильмов в базе данных.
  * Перейти в меню управления пользователями:
  	 * Просмотреть список запросов на подключение, одобрить запрос.
 	 * Просмотреть список всех пользователей
	 * Заблокировать/Разблокировать пользователей
	 * Управлять правами пользователей (Разницы в правах только чтение и чтение и запись нет - не придумал разграничения)
	 * Удалять пользователей


## Настройка и запуск

Для работы Bot(а) требуется:
1. Получить на сайте [Telegram](https://my.telegram.org) api_id и api_hash
2. Зарегистрировать в Telegram через FatherBot нового Bot(a) и получить bot_token, изменить у бота режим /setprivacy на DISABLED
3. Создать новый канал куда будут пересылаться сообщения. Если хотите в конфигурационном файле указывать этот канал по имени, то сделайте канал публичным (public). 
4. Внести настройки в конфигурационный файл *config.py*
5. Изменить имя подгружаемого конфигурационного файла в файле *nnmbot.py*   
6. Запустить скрипт.


## Description
Note: Google translate


Telegram Bot for filtering Telegram channel [NNMCLUB](t.me/nnmclubtor) <br> <br>
A Python script listens to the Telegram channel [NNMCLUB](t.me/nnmclubtor) and forwards messages containing information only about movies to your personal channel. The filter is configured in the configuration file. <br><br>
Bot receives a description of the film from the site https://nnmclub.to and the rating of the film from the site [Kinopoisk](https://www.kinopoisk.ru) and [Imdb](https://www.imdb.com).<br> <br>
Maintains a local database of forwarded messages - films.<br><br>
Excludes duplicate films from forwarding.<br><br>
Currently there are two connections to Telegram. One connection as a user, the second as a Bot. Two connections are used because the Bot cannot listen to channels to which it is not subscribed.

The first connection as a user is used to listen. Using this connection, we receive messages according to the configured filter from the [NNMCLUB](t.me/nnmclubtor) channel and forward it to our personal channel. There the message is picked up by the Bot - the second connection - and attaches control buttons to it - 'Add to DB' and 'Control'.

### Users
New users can apply for registration, after reviewing the application by the administrator, they will have access to:
1. Click the Add button:
* Add (tag) films to the database.
2. Click the Manage button:
* View the list of added movies.
* Clear the list of added movies.
* View previously added and cleared movies.
* Search movies in the database.
* Get information about the database.

### Administrator
Users who are channel Administrators are automatically also bot Administrators.
The procedure for registering as an administrator is similar to that for a user:
1. Apply for connection.
2. Return to the channel and press Control again.
3. In the menu for working with users, approve the request on your own behalf.

Administrators have access to:
1. Click the Add button:
  * Add (mark) films to the database for subsequent work.
2. Click the Manage button:
  * View the list of added movies.
  * Clear the list of added movies.
  * View previously added and cleared movies.
  * Search movies in the database.
  * Get information about the database.
  * Get a list of all movies in the database.
  * Go to user management menu:
  	* View the list of connection requests, approve the request.
 	* View list of all users
	* Block/Unblock users
	* Manage user rights (There are no differences in rights only read and read and write - I didn’t come up with a distinction)
	* Delete users


## Setup and launch

For the Bot to work you need:
1. Get api_id and api_hash on the website [Telegram](https://my.telegram.org)
2. Register a new Bot(a) in Telegram via FatherBot and get a bot_token, change the bot’s /setprivacy mode to DISABLED
3. Create a new channel where messages will be sent. If you want to specify this channel by name in the configuration file, then make the channel public.
4. Make settings in the configuration file *config.py*
5. Change name configuration file in file *nnmbot.py*
6. Run the script.
