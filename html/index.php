<?php

require realpath(__DIR__ . '/../vendor/autoload.php');

$app = new \Slim\App(new \Slim\Container([
    'settings' => [
        'displayErrorDetails' => true,
    ],
]));
$app->config = new \TodoRemind\Config(realpath(__DIR__ . '/../config'));
$app->db = new \TodoRemind\Db(realpath(__DIR__ . '/../db.json'));

function updateTodos($app, $dbxClient) {

    $fd = fopen('php://temp', 'wb');
    $dbxClient->getFile($app->config->item('dropbox')['file_location'], $fd);
    rewind($fd);
    $lines = explode(PHP_EOL, stream_get_contents($fd));
    fclose($fd);

    $now = new DateTime();

    $todos = array_reduce($lines, function ($acc, $todo) use ($now) {
        if (!preg_match('/(.+) notify:(\S+)/', $todo, $matches)) {
            return $acc;
        }

        $text = $matches[1];
        $datetime = DateTime::createFromFormat('Y-m-d-Hi', $matches[2]);

        // Default un-timed items to 8am
        if (!$datetime) {
            $datetime = DateTime::createFromFormat('Y-m-d', $matches[2]);

            if (!$datetime) {
                return $acc;
            }

            $datetime->setTime(8, 0);
        }

        // Do not stage past items
        if ($datetime < $now) {
            return $acc;
        }

        $acc[] = [
            'text'     => $todo,
            'datetime' => $datetime->format('Y-m-d H:i'),
        ];

        return $acc;
    }, []);

    $app->db->update('todos', $todos);

    return $todos;
}

$app->map(['GET', 'POST'], '/sync', function ($request, $response) use ($app) {
    $challenge = $request->getParam('challenge');

    $cursor = $app->db->query('dbx_cursor');

    $dbxClient = new \Dropbox\Client($app->config->item('dropbox')['access_token'], 'Todo-Reminder/1.0');
    $delta = $dbxClient->getDelta($cursor, $app->config->item('dropbox')['file_location']);

    if (!empty($delta['entries'])) {
        $entries = updateTodos($app, $dbxClient);
    }

    $app->db->update('dbx_cursor', $delta['cursor']);

    return $response->write($challenge);
});

$app->get('/debug', function ($request, $response) use ($app) {
    $cursor = $app->db->query('dbx_cursor');

    $dbxClient = new \Dropbox\Client($app->config->item('dropbox')['access_token'], 'Todo-Reminder/1.0');
    $delta = $dbxClient->getDelta($cursor, $app->config->item('dropbox')['file_location']);

    if (!empty($delta['entries'])) {
        $entries = updateTodos($app, $dbxClient);
        $response = $response->withHeader('Content-type', 'application/json');

        return $response->write(json_encode($entries));
    }
});

$app->run();
