<?php include "header.php";
include "config.php"; ?>
<h1>Alertes critiques</h1>

<table>
<tr>
<th>Zone</th>
<th>Niveau</th>
<th>Message</th>
<th>Statut</th>
<th>Date</th>
</tr>

<?php
$sql = "SELECT a.*, z.nom_zone FROM alertes a JOIN zones z ON a.zone_id = z.id";
$result = mysqli_query($conn,$sql);
while($row = mysqli_fetch_assoc($result)){
    echo "<tr>
            <td>{$row['nom_zone']}</td>
            <td class='{$row['niveau_alerte']}'>{$row['niveau_alerte']}</td>
            <td>{$row['message']}</td>
            <td>{$row['statut']}</td>
            <td>{$row['date_alerte']}</td>
          </tr>";
}
?>

</table>
<?php include "footer.php"; ?>