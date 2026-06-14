(function () {
  'use strict';

  var ENDPOINT = '/form.php';
  var THANKS = '/thanks.html';

  function matches(el, selector) {
    var p = Element.prototype;
    var f = p.matches || p.webkitMatchesSelector || p.mozMatchesSelector || p.msMatchesSelector;
    return f && f.call(el, selector);
  }

  function closest(el, selector) {
    while (el && el !== document) {
      if (matches(el, selector)) return el;
      el = el.parentNode;
    }
    return null;
  }

  function textOf(el) {
    return (el && (el.textContent || el.innerText) || '').toLowerCase();
  }

  function isLeadForm(form) {
    if (!form || form.nodeName !== 'FORM') return false;
    if (form.getAttribute('data-kilka-ignore') === '1') return false;
    if (form.querySelector('input[name="phone"], input[name="email"], textarea[name="aboutProject"], textarea[name="message"]')) return true;
    var txt = textOf(form);
    return txt.indexOf('отправить бриф') !== -1 || txt.indexOf('контактные данные') !== -1 || txt.indexOf('быстрая заявка') !== -1;
  }

  function prepareForm(form) {
    if (!isLeadForm(form)) return;
    form.setAttribute('action', ENDPOINT);
    form.setAttribute('method', 'post');
    form.setAttribute('enctype', 'multipart/form-data');
    form.setAttribute('data-kilka-patched', '1');
  }

  function prepareAllForms() {
    var forms = document.querySelectorAll('form');
    for (var i = 0; i < forms.length; i++) prepareForm(forms[i]);
  }

  function addSelectedButtons(fd, form) {
    var services = [];
    var budgets = [];
    var sources = [];
    var all = [];
    var buttons = form.querySelectorAll('button[aria-pressed="true"], .Mui-selected');

    for (var i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      var value = (btn.getAttribute('value') || btn.getAttribute('aria-label') || btn.textContent || '').replace(/^\s+|\s+$/g, '');
      if (!value) continue;
      if (all.indexOf(value) === -1) all.push(value);

      var block = closest(btn, '.BriefForm-module-scss-module__XwLKHW__inner_item');
      var title = '';
      if (block) {
        var h = block.querySelector('h3, h4');
        title = textOf(h);
      }
      if (title.indexOf('услуг') !== -1) services.push(value);
      else if (title.indexOf('бюджет') !== -1) budgets.push(value);
      else if (title.indexOf('откуда') !== -1) sources.push(value);
    }

    if (services.length) fd.append('Услуги', services.join(', '));
    if (budgets.length) fd.append('Бюджет', budgets.join(', '));
    if (sources.length) fd.append('Откуда узнали', sources.join(', '));
    if (all.length) fd.append('Выбранные кнопки', all.join(', '));
  }

  function showError() {
    alert('Не удалось отправить заявку. Напишите, пожалуйста, на kilkasales@kilkamarketing.ru');
  }

  function sendForm(form) {
    if (!isLeadForm(form)) return;
    if (form.getAttribute('data-kilka-sending') === '1') return;

    prepareForm(form);
    form.setAttribute('data-kilka-sending', '1');

    var fd = new FormData(form);
    addSelectedButtons(fd, form);
    fd.append('source', window.location.href);

    var submit = form.querySelector('button[type="submit"], button:not([type])');
    var oldText = submit ? submit.textContent : '';
    if (submit) {
      submit.disabled = true;
      submit.textContent = 'Отправляем...';
    }

    fetch(ENDPOINT, {
      method: 'POST',
      body: fd,
      credentials: 'same-origin',
      cache: 'no-store'
    }).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.text();
    }).then(function () {
      window.location.href = THANKS;
    }).catch(function () {
      form.removeAttribute('data-kilka-sending');
      if (submit) {
        submit.disabled = false;
        submit.textContent = oldText || 'Отправить бриф';
      }
      showError();
    });
  }

  document.addEventListener('submit', function (event) {
    var form = event.target;
    if (!isLeadForm(form)) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    sendForm(form);
  }, true);

  document.addEventListener('click', function (event) {
    var btn = closest(event.target, 'button');
    if (!btn) return;
    var form = closest(btn, 'form');
    if (!isLeadForm(form)) return;
    var type = (btn.getAttribute('type') || 'submit').toLowerCase();
    var text = textOf(btn);
    if (type !== 'submit' && text.indexOf('отправить') === -1) return;

    event.preventDefault();
    event.stopPropagation();
    if (event.stopImmediatePropagation) event.stopImmediatePropagation();
    sendForm(form);
  }, true);

  document.addEventListener('DOMContentLoaded', prepareAllForms);
  prepareAllForms();
  setInterval(prepareAllForms, 800);
})();
