# roskomtools
Набор простых консольных утилит для операторов связи.

* ``rkn-load.py`` — осуществление выгрузки реестра запрещённых сайтов
* ``rkn-check.py`` — проверка качества блокировок

© 2015–2018 ООО «Оргтехсервис» (Илья Аверков, Маргарита Кособокова)

## Сборка и установка

Сначала необходимо сгенерировать deb-пакеты.

```bash
git clone https://github.com/orgtechservice/roskomtools.git
cd roskomtools
./build.sh
```

Затем — установить зависимости и сгенерированные deb-пакеты

```bash
sudo apt install python3 python3-requests python3-suds python3-lxml
sudo dpkg -i rkn-load.deb
sudo dpkg -i rkn-check.deb
```

## Использование

* Подкидываем файлы запроса и подписи в ``/etc/roskom/request.xml`` и ``/etc/roskom/request.xml.sign`` соответственно
* Запускаем ``rkn-load.py``. Будет произведена автоматическая выгрузка и в текущем каталоге появится файл ``dump.xml``.
* Редактируем ``/etc/roskom/config.py``, задаём строку для поиска. По наличию этой подстроки скрипт проверок будет автоматически определять то, что сайт блокируется успешно.
* Запускаем ``rkn-check.py`` в том же каталоге, в котором запускался ``rkn-load.py``. Будет сформирован файл ``result.txt``, содержащий список ссылок, по которым имеются проблемы с блокировками, и отметки времени UNIX, когда данная ссылка открылась. В процессе проверки данные также отображаются в реальном времени в стандартном потоке вывода. Прервать проверку можно нажатием ctrl-c.

## Статусы

* ``blocked`` — Ресурс успешно блокируется, получена страница-заглушка
* ``failure`` — Ресурс успешно блокируется, произошла ошибка TCP
* ``local-ip`` — Ресурс резолвится в локальный IP
* ``available`` — Ресурс **не блокируется**


## Telegram

* Adjust string 202 of ``/usr/bin/rkn-check.py`` with your bot-ID and chat_ID

```
202 cmdstring = "/usr/bin/curl -s -d \"chat_id=-10CHAT-ID57&disable_web_page_preview=1&text=Checked %d, errors: %d\"" % (total_count, available_count) + " https://api.telegram.org/bot36BOT-ID8:AAEBOT-ID9Ksl-6ABOT-IDY0/sendMessage"
203 
204 print (cmdstring)
205 
206 os.system( cmdstring )

```

* ``GET handy tg output as`` - **Checked 121040, errors: 0**


