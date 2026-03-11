<?php
include "config.php";

if(isset($_POST['login'])){

$username = $_POST['username'];
$password = $_POST['password'];

$sql = "SELECT * FROM utilisateurs 
WHERE username='$username' AND password='$password'";

$result = mysqli_query($conn,$sql);

if(mysqli_num_rows($result) == 1){
header("Location: dashboard.php");
}else{
$error="Identifiants incorrects";
}

}
?>

<!DOCTYPE html>
<html>

<head>
<title>CrowdSense JOJ 2026</title>
<link rel="stylesheet" href="style.css">
</head>

<body>

<div class="login-box">

<h2>Connexion Sécurité</h2>

<form method="POST">

<input type="text" name="username" placeholder="Utilisateur" required>

<input type="password" name="password" placeholder="Mot de passe" required>

<button name="login">Se connecter</button>

</form>

<?php if(isset($error)){ echo $error; } ?>

</div>

</body>
</html>