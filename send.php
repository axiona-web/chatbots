<?php
$origin = isset($_SERVER['HTTP_ORIGIN']) ? $_SERVER['HTTP_ORIGIN'] : '';
$allowed = ['https://axiona-group.sk', 'https://www.axiona-group.sk'];
if (in_array($origin, $allowed)) {
    header('Access-Control-Allow-Origin: ' . $origin);
} else {
    header('Access-Control-Allow-Origin: https://axiona-group.sk');
}
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['ok' => false]);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);

$meno    = isset($data['meno'])    ? strip_tags($data['meno'])    : '';
$firma   = isset($data['firma'])   ? strip_tags($data['firma'])   : '';
$email   = isset($data['email'])   ? strip_tags($data['email'])   : '';
$telefon = isset($data['telefon']) ? strip_tags($data['telefon']) : '';
$web     = isset($data['web'])     ? strip_tags($data['web'])     : '';
$sprava  = isset($data['sprava'])  ? strip_tags($data['sprava'])  : '';
$cas     = date('d.m.Y H:i');

$to      = 'office@axiona-group.sk';
$subject = 'Nova ziadost o demo — ' . $meno;
$body    = "Nova ziadost o demo z axiona-group.sk\n\n";
$body   .= "Meno:    $meno\n";
$body   .= "Firma:   $firma\n";
$body   .= "Email:   $email\n";
$body   .= "Telefon: $telefon\n";
$body   .= "Web:     $web\n";
$body   .= "Sprava:  $sprava\n";
$body   .= "Cas:     $cas\n";

$headers  = "From: office@axiona-group.sk\r\n";
$headers .= "Reply-To: $email\r\n";
$headers .= "X-Mailer: PHP\r\n";

$ok = mail($to, $subject, $body, $headers);

echo json_encode(['ok' => $ok]);
