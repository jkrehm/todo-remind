<?php namespace TodoRemind;

class Db
{
    protected $_db;
    protected $_dbFile;

    public function __construct($dbFile)
    {
        $this->_dbFile = $dbFile;
        $this->_db = json_decode(file_get_contents($this->_dbFile), true);
    }

    public function query($key)
    {
        return array_key_exists($key, $this->_db) ? $this->_db[$key] : null;
    }

    public function update($key, $value = null)
    {
        $this->_db[$key] = $value;
    }

    public function __destruct()
    {
        file_put_contents($this->_dbFile, json_encode($this->_db, JSON_PRETTY_PRINT));
    }
}
