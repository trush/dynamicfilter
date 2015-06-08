var start_ms;
var end_ms;

function startTime() {
   start = new Date();
   start_ms = start.getTime();
}

function endTime() {
   end = new Date();
   end_ms = end.getTime();
   var elem = document.getElementById("elapsed_time");
   elem.value = end_ms-start_ms;
}