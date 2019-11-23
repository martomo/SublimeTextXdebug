<?php

function greet(string $name) {
    $greet = 'Hi';
    if ($name === 'Stranger') {
        $greet = 'Hello';
    }
    return "{$greet} {$name}!";
}

$greeting = greet('Stranger');
echo $greeting;
