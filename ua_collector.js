var w = $(window).width();
var h = $(window).height();
var ua = navigator.userAgent;
// initiate xhttp
if (window.XMLHttpRequest) {
   xhttp = new XMLHttpRequest();
} else {
   xhttp = new ActiveXObject("Microsoft.XMLHTTP");
}
// post client resolution
xhttp.open("POST", "ua.php", false);
xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
xhttp.send("client=1&w=" + w + "&h=" + h + "&ua=" + ua);
