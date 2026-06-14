/* Яндекс.Метрика для kilkamarketing.ru — счётчик 109805845.
   Подключается одним тегом <script src="/metrika.js" defer> на всех страницах,
   поэтому код не дублируется. <noscript>-пиксель добавлен в HTML каждой страницы. */
(function (m, e, t, r, i, k, a) {
  m[i] = m[i] || function () { (m[i].a = m[i].a || []).push(arguments); };
  m[i].l = 1 * new Date();
  for (var j = 0; j < document.scripts.length; j++) { if (document.scripts[j].src === r) { return; } }
  k = e.createElement(t), a = e.getElementsByTagName(t)[0], k.async = 1, k.src = r, a.parentNode.insertBefore(k, a);
})(window, document, 'script', 'https://mc.yandex.ru/metrika/tag.js?id=109805845', 'ym');

ym(109805845, 'init', {
  ssr: true,
  webvisor: true,
  clickmap: true,
  ecommerce: "dataLayer",
  referrer: document.referrer,
  url: location.href,
  accurateTrackBounce: true,
  trackLinks: true
});

/* Цель «lead_form» — отправка любой формы заявки */
document.addEventListener('submit', function (ev) {
  if (ev.target && ev.target.tagName === 'FORM') {
    try { ym(109805845, 'reachGoal', 'lead_form'); } catch (e) {}
  }
}, true);
