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
header('Content-Type: application/json; charset=UTF-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['ok' => false]);
    exit;
}

date_default_timezone_set('Europe/Bratislava');

$data = json_decode(file_get_contents('php://input'), true);
if (!is_array($data)) {
    $data = [];
}

// Honeypot: vyplnené skryté pole company_website = robot → rovnaká úspešná odpoveď, e-mail sa neodošle
if (isset($data['company_website']) && is_scalar($data['company_website']) && trim((string) $data['company_website']) !== '') {
    echo json_encode(['ok' => true]);
    exit;
}

// Text z formulára: bez HTML značiek, orezaný
function field($data, $key) {
    return isset($data[$key]) && is_scalar($data[$key]) ? trim(strip_tags((string) $data[$key])) : '';
}
// Hodnota do hlavičky e-mailu: bez zalomení riadkov (ochrana proti vloženiu ďalších hlavičiek)
function header_safe($value) {
    return trim(str_replace(["\r", "\n"], ' ', $value));
}
// UTF-8 hlavička podľa RFC 2047
function mime_utf8($value) {
    return '=?UTF-8?B?' . base64_encode($value) . '?=';
}

$zdroj          = field($data, 'zdroj');
$meno           = field($data, 'meno');
$firma          = field($data, 'firma');
$email          = field($data, 'email');
$telefon        = field($data, 'telefon');
$web            = field($data, 'web');
$pocet_maklerov = field($data, 'pocet_maklerov');
$sprava         = field($data, 'sprava');
$stranka        = field($data, 'stranka');
$cas            = date('d.m.Y H:i');

$clen_ru = null;
if (array_key_exists('clen_ru', $data)) {
    $v = $data['clen_ru'];
    $clen_ru = ($v === true || $v === 1 || $v === '1' || $v === 'true' || $v === 'áno') ? 'áno' : 'nie';
}

$to      = 'office@axiona-group.sk';
$subject = mime_utf8(header_safe('Nový dopyt – ' . ($zdroj !== '' ? $zdroj : 'web') . ' – ' . $meno));

// Povinné polia (meno, firma, e-mail, telefón), zdroj a čas sú vždy; ostatné len ak sú vyplnené
$lines = [
    ['Zdroj',          $zdroj !== '' ? $zdroj : 'web', true],
    ['Meno',           $meno,           true],
    ['Firma',          $firma,          true],
    ['E-mail',         $email,          true],
    ['Telefón',        $telefon,        true],
    ['Web',            $web,            false],
    ['Počet maklérov', $pocet_maklerov, false],
    ['Člen RÚ',        $clen_ru === null ? '' : $clen_ru, false],
    ['Správa',         $sprava,         false],
    ['Stránka',        $stranka,        false],
    ['Čas',            $cas,            true],
];

$body = "Nový dopyt z axiona-group.sk\n\n";
foreach ($lines as $l) {
    if ($l[2] || $l[1] !== '') {
        $body .= $l[0] . ': ' . wordwrap($l[1], 900, "\n", true) . "\n";
    }
}

$headers  = "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
$headers .= "Content-Transfer-Encoding: 8bit\r\n";
$headers .= "From: office@axiona-group.sk\r\n";
$reply = header_safe($email);
if (filter_var($reply, FILTER_VALIDATE_EMAIL)) {
    $headers .= "Reply-To: $reply\r\n";
}
$headers .= "X-Mailer: PHP\r\n";

// Lokálny test: AXIONA_MAIL_DUMP=/cesta/subor.txt zapíše e-mail do súboru namiesto odoslania
$dump = getenv('AXIONA_MAIL_DUMP');
if ($dump) {
    $ok = file_put_contents($dump, "To: $to\r\nSubject: $subject\r\n$headers\r\n$body") !== false;
} else {
    $ok = mail($to, $subject, $body, $headers);
}

echo json_encode(['ok' => $ok]);
