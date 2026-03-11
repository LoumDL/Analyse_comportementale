<?php include "header.php"; 
include "config.php";?>
<h1>Zones du site</h1>

<table>
<tr>
<th>ID</th>
<th>Nom de la zone</th>
<th>Capacité maximale</th>
</tr>

<?php
$sql = "SELECT * FROM zones";
$result = mysqli_query($conn,$sql);
while($row = mysqli_fetch_assoc($result)){
    echo "<tr>
            <td>{$row['id']}</td>
            <td>{$row['nom_zone']}</td>
            <td>{$row['capacite_max']}</td>
          </tr>";
}
?>

</table>
<?php include "footer.php"; ?>