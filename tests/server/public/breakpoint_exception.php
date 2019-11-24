<?php

class Deprecated {

    private function __construct() {}

    function get()
    {
        self::__construct();
    }
}

$exception = $_GET['exception'] ?? '';
switch ($exception) {
    case 'Deprecated':
        Deprecated::get();
        break;
    case 'Notice':
        echo $notice;
        break;
    case 'Parse error':
        include 'breakpoint_exception_parse_error.php';
        break;
    case 'Warning':
        include 'breakpoint_exception_warning.php';
        break;
    default:
        throw new Exception("I'm sorry Dave, I'm afraid I can't do that.");
}
