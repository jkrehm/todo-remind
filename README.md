# Overview

Accepts webhook requests from Dropbox to update the list of ToDo items that
require notifications.

# Requirements

* Python 3.4+
* Dropbox developer account 

# Setup

* Create a virtual environment, e.g. `virtualenv venv`.
* Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate`
  (Linux/macOS).
* Run `pip install -r requirements.txt`.
* Run `flask run` to start the application.
* Navigate to [http://127.0.0.1:5000/config](http://127.0.0.1:5000/config) 
  and populate the configuration items.
* Navigate to [http://127.0.0.1:5000/debug](http://127.0.0.1:5000/debug) 
  to verify todo items are getting populated.
* Configure Dropbox to send webhook requests to the `/sync` route.
* Run `FLASK_APP=/path/to/todo.py flask notify` to run the notifier.

# Reverse Proxy

## Apache

```
<VirtualHost *:443>
    ServerName todo-remind.example.com

    <Location "/" >
        RequestHeader set X-SCHEME https
        ProxyPass http://localhost:8088/
        ProxyPassReverse http://localhost:8088/
    </Location>

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/todo-remind.example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/todo-remind.example.com/privkey.pem
</VirtualHost>
```

# Systemctl

```
[Unit]
Description=todo-remind

[Service]
Type=simple
User=jonathan
WorkingDirectory=/path/to/todo-remind
ExecStart=/path/to/todo-remind/venv/bin/waitress-serve --listen=localhost:8088 --call todo_remind:create_app
Environment=SECRET_KEY=<secret_key>

[Install]
WantedBy=multi-user.target
```
