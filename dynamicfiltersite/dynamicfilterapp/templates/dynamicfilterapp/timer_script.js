function startTime() {
    var start=new Date();
    m = checkTime(m);
    s = checkTime(s);
}

function checkTime(i) {
    if (i<10) {i = "0" + i};  // add zero in front of numbers < 10
    return i;
}