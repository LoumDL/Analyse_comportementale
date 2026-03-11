<?php

$host = "localhost";
$user = "root";
$password = "";
$dbname = "crowdsense";

$conn = mysqli_connect($host,$user,$password,$dbname);

if(!$conn){
die("Connexion échouée");
}

?>