<?php
// pages/calendar.php
require '../config/db.php';
include '../includes/header.php';

$events = [];

try {
    // 1. Follow-Ups
    $stmt = $pdo->query("SELECT f.id, f.lead_id, f.follow_up_date, f.status, l.title as lead_title FROM FollowUps f JOIN Leads l ON f.lead_id = l.id");
    while ($row = $stmt->fetch()) {
        $color = ($row['status'] == 'Completed') ? '#198754' : (($row['status'] == 'Cancelled') ? '#dc3545' : '#ffc107');
        $textColor = ($row['status'] == 'Pending') ? '#000' : '#fff';
        
        $events[] = [
            'id' => 'f_'.$row['id'],
            'title' => 'Follow-up: ' . $row['lead_title'],
            'start' => $row['follow_up_date'],
            'url' => 'followup_edit.php?id=' . $row['id'],
            'backgroundColor' => $color,
            'borderColor' => $color,
            'textColor' => $textColor,
            'allDay' => true
        ];
    }

    // 2. Deals Expected Close Dates
    $stmt = $pdo->query("SELECT id, title, expected_close_date, stage FROM Deals WHERE expected_close_date IS NOT NULL");
    while ($row = $stmt->fetch()) {
        $color = ($row['stage'] == 'Closed Won') ? '#198754' : (($row['stage'] == 'Closed Lost') ? '#dc3545' : '#0d6efd');
        $events[] = [
            'id' => 'd_'.$row['id'],
            'title' => 'Closing Deal: ' . $row['title'],
            'start' => $row['expected_close_date'],
            'url' => 'deal_edit.php?id=' . $row['id'],
            'backgroundColor' => $color,
            'borderColor' => $color,
            'allDay' => true
        ];
    }
} catch (PDOException $e) {
    echo "<div class='alert alert-danger'>Error loading calendar: " . $e->getMessage() . "</div>";
}
?>

<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>Task & Deadline Calendar</h2>
    <a href="../dashboard.php" class="btn btn-secondary"><i class="bi bi-arrow-left"></i> Back to Dashboard</a>
</div>

<div class="card shadow-sm border-top border-primary border-4 mb-4">
    <div class="card-body p-4">
        <div id="calendar"></div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        themeSystem: 'bootstrap5',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,listWeek'
        },
        events: <?= json_encode($events) ?>,
        eventClick: function(info) {
            if (info.event.url) {
                window.location.href = info.event.url;
                info.jsEvent.preventDefault(); // don't let the browser navigate normally
            }
        }
    });
    calendar.render();
});
</script>

<style>
/* Fullcalendar Custom Adjustments */
.fc-event { cursor: pointer; border-radius: 4px; padding: 2px 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
.fc-toolbar-title { font-weight: 700 !important; color: #333; }
.fc .fc-button-primary { background-color: #0d6efd; border-color: #0d6efd; }
.fc .fc-button-primary:hover { background-color: #0b5ed7; border-color: #0a58ca; }
</style>

<?php include '../includes/footer.php'; ?>
