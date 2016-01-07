<?php namespace TodoRemind;

class Config
{
    protected $_config;
    protected $_configDirectory;

    public function __construct($configDirectory)
    {
        $this->_configDirectory = $configDirectory;
        $this->_config = [
            'dropbox'    => json_decode(file_get_contents($this->_configDirectory . '/dropbox.json'), true),
            'pushbullet' => json_decode(file_get_contents($this->_configDirectory . '/pushbullet.json'), true),
        ];
    }

    public function item($key, $value = null)
    {
        if (is_null($value)) {
            return array_key_exists($key, $this->_config) ? $this->_config[$key] : null;
        } else {
            $this->_config[$key] = $value;
        }
    }

    public function __destruct()
    {
        file_put_contents($this->_configDirectory . '/dropbox.json', json_encode($this->_config['dropbox'], JSON_PRETTY_PRINT));
        file_put_contents($this->_configDirectory . '/pushbullet.json', json_encode($this->_config['pushbullet'], JSON_PRETTY_PRINT));
    }
}
