<?php

//CREATE TABLE clients(hash VARCHAR(32), w INT(4), h INT(4), ua VARCHAR(255));

function validate_str($input, $link) {
    return mysqli_real_escape_string($link, $input);
}

function validate_int($input, $link) {
    $num = mysqli_real_escape_string($link, strip_tags(escapeshellcmd($input)));
    if(is_numeric($num)||($num == "")) {
        return (int) $num;
    } else {
        die("Input parameter not a number");
    }
}

class db {
    var $link;
	var $db_host = "";
	var $db_user = "";
	var $db_pass = "";
	var $db_name = "";

    function connect() {
        $this->db = new mysqli($this->db_host, $this->db_user, $this->db_pass, $this->db_name);
        $this->prfx = $db_prfx;
    }

    function close() {
        $this->db->close();
    }

	function existshash($hash) {
		$result = $this->db->query($k = "SELECT hash FROM clients WHERE hash = '$hash'");
		if (mysqli_num_rows($result) == 1) {
			return true;
		} else {
			return false;
		}
	}

    function addua($hash, $w, $h, $ua) {
        $this->db->query("INSERT INTO clients VALUES('$hash', $w, $h, '$ua')");
    }
}

$mydb = new db();
$mydb->connect();

// process client data
if ((isset($_REQUEST["client"])) && ($_REQUEST["client"] == 1)) {
	$w = validate_int($_POST["w"], $mydb->db);
	$h = validate_int($_POST["h"], $mydb->db);
	$ua = validate_str($_POST["ua"], $mydb->db);
    $ip = $_SERVER['REMOTE_ADDR'];
	$hash = md5($ip);

	// add if not already added
	if (!$mydb->existshash($hash)) {
		$mydb->addua($hash, $w, $h, $ua);
	}
}
?>
