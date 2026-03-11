<?php include "header.php";
include "config.php"; ?>
<h1>Analyse des risques</h1>

<table>
<tr>
<th>Zone</th>
<th>Niveau de risque</th>
<th>Description</th>
<th>Date</th>
</tr>

<?php
$sql = "SELECT r.*, z.nom_zone FROM risques r JOIN zones z ON r.zone_id = z.id";
$result = mysqli_query($conn,$sql);
while($row = mysqli_fetch_assoc($result)){
    echo "<tr>
            <td>{$row['nom_zone']}</td>
            <td class='{$row['niveau_risque']}'>{$row['niveau_risque']}</td>
            <td>{$row['description']}</td>
            <td>{$row['date_risque']}</td>
          </tr>";
}
?>

</table>
<?php include "footer.php"; ?>