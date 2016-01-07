# Setup

- Run `composer install`.
- Populate the configuration files found in `/config`.
- Point a web server at the `/html` directory. Make sure it directs all requests at the `index.php` file.
- Create a Dropbox application and add a webhook that calls `<site>/sync`.
- Create a cron entry that runs `php /path/to/dir/remind.php` every minute.