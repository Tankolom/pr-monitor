<?php
/*
 * Kilka Marketing lead form handler
 * PHP 5.6 compatible.
 * Sends leads by SMTP via Yandex and saves backup to /leads/leads.csv
 */

/* Безопасная самодиагностика доставки (секретный ключ, токен не раскрывается).
   Открыть: /form.php?diag=kilka-7f3a9c2b . Удалить этот блок после настройки можно, но не обязательно. */
if (isset($_GET['diag']) && $_GET['diag'] === 'kilka-7f3a9c2b') {
    header('Content-Type: application/json; charset=UTF-8');
    $cfgFile = __DIR__ . '/mail_config.php';
    $cfg = file_exists($cfgFile) ? include $cfgFile : array();
    $tok = isset($cfg['telegram_token']) ? trim($cfg['telegram_token']) : '';
    $out = array(
        'php' => PHP_VERSION,
        'curl' => function_exists('curl_init'),
        'allow_url_fopen' => (bool)ini_get('allow_url_fopen'),
        'config_found' => file_exists($cfgFile),
        'telegram_token_set' => ($tok !== '' && $tok !== 'PASTE_BOT_TOKEN_HERE'),
        'telegram_chat_set' => !empty($cfg['telegram_chat_id']),
        'smtp_pass_set' => (isset($cfg['smtp_pass']) && $cfg['smtp_pass'] !== '' && $cfg['smtp_pass'] !== 'PASTE_APP_PASSWORD_HERE')
    );
    if ($out['telegram_token_set']) {
        $url = 'https://api.telegram.org/bot' . $tok . '/getMe';
        if (function_exists('curl_init')) {
            $ch = curl_init($url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
            curl_setopt($ch, CURLOPT_TIMEOUT, 12);
            $r = curl_exec($ch);
            $out['telegram_reachable'] = ($r !== false && strpos((string)$r, '"ok":true') !== false);
            $out['telegram_http'] = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            $out['telegram_error'] = ($r === false) ? curl_error($ch) : '';
            curl_close($ch);
        } else {
            $ctx = stream_context_create(array('http' => array('timeout' => 12, 'ignore_errors' => true)));
            $r = @file_get_contents($url, false, $ctx);
            $out['telegram_reachable'] = ($r !== false && strpos((string)$r, '"ok":true') !== false);
            $out['telegram_error'] = ($r === false) ? 'file_get_contents failed (allow_url_fopen/блокировка)' : '';
        }
    }
    $shost = isset($cfg['smtp_host']) ? $cfg['smtp_host'] : 'smtp.yandex.ru';
    $sport = isset($cfg['smtp_port']) ? intval($cfg['smtp_port']) : 465;
    $serrno = 0; $serrstr = '';
    $sfp = @fsockopen('ssl://' . $shost, $sport, $serrno, $serrstr, 12);
    if ($sfp) { $out['smtp_reachable'] = true; @fclose($sfp); }
    else { $out['smtp_reachable'] = false; $out['smtp_error'] = $serrno . ' ' . $serrstr; }
    echo json_encode($out);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    header('Content-Type: text/plain; charset=UTF-8');
    echo 'Method not allowed';
    exit;
}

$subject = 'Новая заявка с сайта kilkamarketing.ru';

function kilka_clean($value) {
    if (is_array($value)) {
        $result = array();
        foreach ($value as $v) {
            $result[] = kilka_clean($v);
        }
        return implode(', ', $result);
    }
    $value = trim((string)$value);
    $value = strip_tags($value);
    $value = str_replace(array("\r\n", "\r"), "\n", $value);
    return $value;
}

function kilka_first($names) {
    foreach ($names as $name) {
        if (isset($_POST[$name])) {
            $value = kilka_clean($_POST[$name]);
            if ($value !== '') { return $value; }
        }
    }
    return '';
}

function kilka_json($ok, $message, $extra) {
    header('Content-Type: application/json; charset=UTF-8');
    $data = array('ok' => $ok ? true : false, 'message' => $message);
    foreach ($extra as $k => $v) { $data[$k] = $v; }
    echo json_encode($data);
    exit;
}

function kilka_log_error($message) {
    $leadDir = __DIR__ . '/leads';
    if (!is_dir($leadDir)) { @mkdir($leadDir, 0755, true); }
    kilka_protect_dir($leadDir);
    @file_put_contents($leadDir . '/smtp_error.log', '[' . date('Y-m-d H:i:s') . '] ' . $message . "\n", FILE_APPEND);
}

function smtp_read_response($fp) {
    $data = '';
    while (!feof($fp)) {
        $line = fgets($fp, 515);
        if ($line === false) { break; }
        $data .= $line;
        if (strlen($line) >= 4 && substr($line, 3, 1) === ' ') { break; }
    }
    return $data;
}

function smtp_code($response) {
    return intval(substr($response, 0, 3));
}

function smtp_expect($fp, $expected, $context) {
    $response = smtp_read_response($fp);
    $code = smtp_code($response);
    $ok = false;
    if (is_array($expected)) {
        $ok = in_array($code, $expected);
    } else {
        $ok = ($code === $expected);
    }
    if (!$ok) {
        throw new Exception($context . ' failed: ' . trim($response));
    }
    return $response;
}

function smtp_command($fp, $command, $expected, $context) {
    fwrite($fp, $command . "\r\n");
    return smtp_expect($fp, $expected, $context);
}

function smtp_header_encode($text) {
    return '=?UTF-8?B?' . base64_encode($text) . '?=';
}

function smtp_address($email) {
    return str_replace(array("\r", "\n", '<', '>'), '', trim($email));
}

function smtp_send_yandex($config, $subject, $body, $replyTo) {
    $host = isset($config['smtp_host']) ? $config['smtp_host'] : 'smtp.yandex.ru';
    $port = isset($config['smtp_port']) ? intval($config['smtp_port']) : 465;
    $user = isset($config['smtp_user']) ? trim($config['smtp_user']) : '';
    $pass = isset($config['smtp_pass']) ? trim($config['smtp_pass']) : '';
    $pass = str_replace(' ', '', $pass); // Яндекс часто показывает пароль приложения группами через пробелы
    $fromEmail = isset($config['from_email']) ? smtp_address($config['from_email']) : $user;
    $fromName = isset($config['from_name']) ? $config['from_name'] : 'Kilka Marketing';
    $toEmail = isset($config['to_email']) ? smtp_address($config['to_email']) : $user;

    if ($user === '' || $pass === '' || $pass === 'PASTE_APP_PASSWORD_HERE') {
        throw new Exception('SMTP password is not configured in mail_config.php');
    }
    if (!filter_var($user, FILTER_VALIDATE_EMAIL) || !filter_var($toEmail, FILTER_VALIDATE_EMAIL) || !filter_var($fromEmail, FILTER_VALIDATE_EMAIL)) {
        throw new Exception('Invalid SMTP email configuration');
    }

    $errno = 0;
    $errstr = '';
    $fp = @fsockopen('ssl://' . $host, $port, $errno, $errstr, 25);
    if (!$fp) {
        throw new Exception('SMTP connection failed: ' . $errno . ' ' . $errstr);
    }
    stream_set_timeout($fp, 25);

    try {
        smtp_expect($fp, 220, 'Connect');
        smtp_command($fp, 'EHLO kilkamarketing.ru', 250, 'EHLO');
        smtp_command($fp, 'AUTH LOGIN', 334, 'AUTH LOGIN');
        smtp_command($fp, base64_encode($user), 334, 'AUTH USER');
        smtp_command($fp, base64_encode($pass), 235, 'AUTH PASS');
        smtp_command($fp, 'MAIL FROM:<' . $fromEmail . '>', 250, 'MAIL FROM');
        smtp_command($fp, 'RCPT TO:<' . $toEmail . '>', array(250, 251), 'RCPT TO');
        smtp_command($fp, 'DATA', 354, 'DATA');

        $headers = array();
        $headers[] = 'Date: ' . date('r');
        $headers[] = 'From: ' . smtp_header_encode($fromName) . ' <' . $fromEmail . '>';
        $headers[] = 'To: <' . $toEmail . '>';
        $headers[] = 'Subject: ' . smtp_header_encode($subject);
        $headers[] = 'MIME-Version: 1.0';
        $headers[] = 'Content-Type: text/plain; charset=UTF-8';
        $headers[] = 'Content-Transfer-Encoding: base64';
        $headers[] = 'Message-ID: <' . time() . '.' . mt_rand(1000, 9999) . '@kilkamarketing.ru>';
        if ($replyTo !== '' && filter_var($replyTo, FILTER_VALIDATE_EMAIL)) {
            $headers[] = 'Reply-To: <' . smtp_address($replyTo) . '>';
        }

        $message = implode("\r\n", $headers) . "\r\n\r\n" . chunk_split(base64_encode($body));
        $message = str_replace("\n.", "\n..", $message);
        fwrite($fp, $message . "\r\n.\r\n");
        smtp_expect($fp, 250, 'END DATA');
        @smtp_command($fp, 'QUIT', 221, 'QUIT');
        fclose($fp);
        return true;
    } catch (Exception $e) {
        fclose($fp);
        throw $e;
    }
}

/* Возвращает 'ok' | 'fail' | 'fail-connect' (до сервера не достучались — нет смысла пробовать остальные чаты) */
function kilka_telegram_post($url, $params) {
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($params));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
        curl_setopt($ch, CURLOPT_TIMEOUT, 12);
        $res = curl_exec($ch);
        $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $errno = curl_errno($ch);
        curl_close($ch);
        if ($res !== false && $code >= 200 && $code < 300) { return 'ok'; }
        /* 6 = не резолвится DNS, 7 = connect failed, 28 = таймаут */
        return in_array($errno, array(6, 7, 28)) ? 'fail-connect' : 'fail';
    }
    $ctx = stream_context_create(array('http' => array(
        'method' => 'POST',
        'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
        'content' => http_build_query($params),
        'timeout' => 12,
        'ignore_errors' => true
    )));
    $res = @file_get_contents($url, false, $ctx);
    if ($res === false) { return 'fail-connect'; }
    return (strpos((string)$res, '"ok":true') !== false) ? 'ok' : 'fail';
}

function kilka_send_telegram($config, $text) {
    $token = isset($config['telegram_token']) ? trim($config['telegram_token']) : '';
    $chats = isset($config['telegram_chat_id']) ? $config['telegram_chat_id'] : '';
    if ($token === '' || $token === 'PASTE_BOT_TOKEN_HERE' || $chats === '') {
        return false;
    }
    if (!is_array($chats)) {
        $chats = preg_split('/[\s,;]+/', trim((string)$chats));
    }
    /* Лимит Telegram на сообщение — 4096 символов */
    if (function_exists('mb_substr')) {
        if (mb_strlen($text, 'UTF-8') > 3900) { $text = mb_substr($text, 0, 3900, 'UTF-8') . "\n…(обрезано)"; }
    } elseif (strlen($text) > 3900) {
        $text = substr($text, 0, 3900) . "\n...(truncated)";
    }
    $url = 'https://api.telegram.org/bot' . $token . '/sendMessage';
    $anyOk = false;
    foreach ($chats as $chat) {
        $chat = trim((string)$chat);
        if ($chat === '') { continue; }
        $status = kilka_telegram_post($url, array(
            'chat_id' => $chat,
            'text' => $text,
            'disable_web_page_preview' => 'true'
        ));
        if ($status === 'ok') { $anyOk = true; }
        if ($status === 'fail-connect') { break; } /* хостинг блокирует Telegram — не держим посетителя */
    }
    if (!$anyOk) {
        kilka_log_error('Telegram: delivery failed (' . (isset($status) ? $status : 'no chats') . ')');
    }
    return $anyOk;
}

function kilka_protect_dir($dir) {
    $guard = $dir . '/.htaccess';
    if (!file_exists($guard)) {
        @file_put_contents($guard, "Require all denied\n<IfModule !mod_authz_core.c>\nOrder allow,deny\nDeny from all\n</IfModule>\n");
    }
    $idx = $dir . '/index.html';
    if (!file_exists($idx)) { @file_put_contents($idx, ''); }
}

/* Honeypot */
if (isset($_POST['website']) && trim($_POST['website']) !== '') {
    kilka_json(true, 'ok', array('spam' => true));
}

$name = kilka_first(array('name', 'Имя', 'your-name', 'client_name'));
$phone = kilka_first(array('phone', 'Телефон', 'tel', 'your-phone', 'client_phone'));
$company = kilka_first(array('company', 'Компания', 'organization', 'client_company'));
$email = kilka_first(array('email', 'Email', 'mail', 'your-email', 'client_email'));
$message = kilka_first(array('aboutProject', 'message', 'project', 'О проекте', 'comment', 'Комментарий', 'brief', 'description'));

$body = "Новая заявка с сайта kilkamarketing.ru\n\n";
$body .= "Имя: " . ($name !== '' ? $name : 'не указано') . "\n";
$body .= "Телефон: " . ($phone !== '' ? $phone : 'не указан') . "\n";
$body .= "Компания: " . ($company !== '' ? $company : 'не указана') . "\n";
$body .= "Email: " . ($email !== '' ? $email : 'не указан') . "\n";
$body .= "О проекте: " . ($message !== '' ? $message : 'не указано') . "\n\n";

$body .= "Все поля формы:\n";
foreach ($_POST as $key => $value) {
    if ($key === 'website') { continue; }
    $cleanKey = kilka_clean($key);
    $cleanValue = kilka_clean($value);
    if ($cleanValue !== '') {
        $body .= $cleanKey . ': ' . $cleanValue . "\n";
    }
}

$body .= "\nСтраница: " . (isset($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : 'не определена');
$body .= "\nIP: " . (isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : 'не определён');
$body .= "\nДата: " . date('d.m.Y H:i:s');

/* Backup to CSV */
$saved = false;
$leadDir = __DIR__ . '/leads';
if (!is_dir($leadDir)) { @mkdir($leadDir, 0755, true); }
kilka_protect_dir($leadDir);
$leadFile = $leadDir . '/leads.csv';
$row = array(
    date('Y-m-d H:i:s'),
    $name,
    $phone,
    $company,
    $email,
    $message,
    isset($_SERVER['HTTP_REFERER']) ? $_SERVER['HTTP_REFERER'] : '',
    isset($_SERVER['REMOTE_ADDR']) ? $_SERVER['REMOTE_ADDR'] : ''
);
$needHeader = !file_exists($leadFile);
$fh = @fopen($leadFile, 'a');
if ($fh) {
    if ($needHeader) { fputcsv($fh, array('date', 'name', 'phone', 'company', 'email', 'message', 'page', 'ip'), ';'); }
    fputcsv($fh, $row, ';');
    fclose($fh);
    $saved = true;
}

$configFile = __DIR__ . '/mail_config.php';
$config = file_exists($configFile) ? include $configFile : array();

/* Канал 1: мгновенно в Telegram (если настроен бот) */
$telegramSent = false;
try {
    $telegramSent = kilka_send_telegram($config, $body);
} catch (Exception $e) {
    kilka_log_error('Telegram: ' . $e->getMessage());
}

/* Канал 2: e-mail через SMTP Яндекса (если задан пароль приложения) */
$mailSent = false;
try {
    smtp_send_yandex($config, $subject, $body, $email);
    $mailSent = true;
} catch (Exception $e) {
    kilka_log_error('SMTP: ' . $e->getMessage());
}

/* Заявка принята, если доставлена хотя бы одним каналом ИЛИ сохранена в бэкап.
   Так посетитель всегда получает подтверждение, а заявка не теряется,
   даже пока не настроены Telegram/SMTP. */
if ($mailSent || $telegramSent || $saved) {
    kilka_json(true, 'ok', array('mail' => $mailSent, 'telegram' => $telegramSent, 'saved' => $saved));
} else {
    http_response_code(500);
    kilka_json(false, 'Не удалось принять заявку', array('mail' => false, 'telegram' => false, 'saved' => false));
}
?>
