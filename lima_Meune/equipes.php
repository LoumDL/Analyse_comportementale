<?php include "header.php";
include "config.php"; ?>
<h1>Équipes de sécurité</h1>

<table>
<tr>
<th>ID</th>
<th>Nom</th>
<th>Responsable</th>
<th>Téléphone</th>
</tr>

<?php
$sql = "SELECT * FROM equipes";
$result = mysqli_query($conn,$sql);
while($row = mysqli_fetch_assoc($result)){
    echo "<tr>
            <td>{$row['id']}</td>
            <td>{$row['nom_equipe']}</td>
            <td>{$row['responsable']}</td>
            <td>{$row['telephone']}</td>
          </tr>";
}
?>

</table>
<?php include "footer.php"; ?>