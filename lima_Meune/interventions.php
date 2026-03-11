<?php include "header.php";
include "config.php"; ?>
<h1>Interventions des équipes</h1>

<table>
<tr>
<th>Équipe</th>
<th>Zone</th>
<th>Description</th>
<th>Statut</th>
<th>Date</th>
</tr>

<?php
$sql = "SELECT i.*, e.nom_equipe, z.nom_zone 
        FROM interventions i 
        JOIN equipes e ON i.equipe_id = e.id 
        JOIN zones z ON i.zone_id = z.id";
$result = mysqli_query($conn,$sql);
while($row = mysqli_fetch_assoc($result)){
    echo "<tr>
            <td>{$row['nom_equipe']}</td>
            <td>{$row['nom_zone']}</td>
            <td>{$row['description']}</td>
            <td>{$row['statut']}</td>
            <td>{$row['date_intervention']}</td>
          </tr>";
}
?>

</table>
<?php include "footer.php"; ?>