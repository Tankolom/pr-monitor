<?php
/*
 * Настройки доставки заявок с форм сайта kilkamarketing.ru.
 * Файл открывается ТОЛЬКО на хостинге, в браузере он недоступен (закрыт .htaccess).
 * Достаточно настроить ЛЮБОЙ из двух каналов (можно оба):
 *
 *  A) Telegram (проще всего, заявки приходят мгновенно):
 *     1. Напишите @BotFather в Telegram → команда /newbot → получите токен.
 *     2. Напишите своему боту любое сообщение, затем узнайте chat_id у @userinfobot.
 *     3. Впишите токен и chat_id ниже.
 *
 *  B) E-mail через Яндекс SMTP:
 *     1. Создайте пароль ПРИЛОЖЕНИЯ в Яндекс ID (не основной пароль почты).
 *     2. Впишите его вместо PASTE_APP_PASSWORD_HERE.
 *     ВАЖНО: старый пароль был скомпрометирован — используйте НОВЫЙ.
 */
return array(
    // --- E-mail (Яндекс SMTP) ---
    'smtp_host' => 'smtp.yandex.ru',
    'smtp_port' => 465,
    'smtp_user' => 'kilkasales@kilkamarketing.ru',
    'smtp_pass' => 'qpwdxpddssclftgl',
    'from_email' => 'kilkasales@kilkamarketing.ru',
    'from_name' => 'Kilka Marketing',
    'to_email' => 'kilkasales@kilkamarketing.ru',

    // --- Telegram (активный канал: заявки приходят сюда мгновенно) ---
    // Бот @Kilkamarketing_bot. Получатели: Leonid (@Leoconsulting) и Dmitriy (@UsachevDE).
    // Чтобы добавить ещё получателя: пусть напишет боту /start и добавьте его chat_id в массив.
    'telegram_token' => '8422564604:AAHowrOH6gW1Hnlu7CziEXgS1R5kJnpfDTU',
    'telegram_chat_id' => array('5534635059', '198486718')
);
?>
