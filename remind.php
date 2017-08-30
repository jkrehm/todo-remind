#!/bin/env php

<?php

require realpath(__DIR__ . '/vendor/autoload.php');

$config = new \TodoRemind\Config(realpath(__DIR__ . '/config'));
$db = new \TodoRemind\Db(realpath(__DIR__ . '/db.json'));
$pb = new \Pushbullet\Pushbullet($config->item('pushbullet')['access_token']);

$todos = $db->query('todos') ?: [];

foreach ($todos as $todo) {
    $now = new DateTime();

    if ($now->format('Y-m-d H:i') === $todo['datetime']) {
        $pb->allDevices()->pushNote('Todo Reminder', $todo['text']);
    }
}
