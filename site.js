// ===== Axiona Group — shared site JS =====
var EMAIL   = 'office@axiona-group.sk';
var WEBHOOK = 'https://hook.eu1.make.com/5yr4gbeogvggl1jyiywhr1rhhjdbz9nf';

document.addEventListener('DOMContentLoaded', function(){
  var cel = document.getElementById('contact-email-link');
  if(cel){ cel.href = 'mailto:' + EMAIL; cel.textContent = EMAIL; }
});

function scroll2(id){ var el = document.getElementById(id); if(el) el.scrollIntoView({behavior:'smooth'}); }

// FAQ (page defines window.FAQS before including this file)
(function(){
  var faqList = document.getElementById('faq-list');
  if(!faqList || !window.FAQS) return;
  window.FAQS.forEach(function(f){
    var item = document.createElement('div');
    item.className = 'faq-item';
    item.innerHTML = '<div class="faq-q" onclick="toggleFaq(this)"><span>' + f.q + '</span><span class="faq-arrow">+</span></div>' +
      '<div class="faq-a">' + f.a + '</div>';
    faqList.appendChild(item);
  });
})();
function toggleFaq(el){
  var a = el.nextElementSibling;
  var open = el.classList.contains('open');
  document.querySelectorAll('.faq-q').forEach(function(q){ q.classList.remove('open'); q.nextElementSibling.classList.remove('open'); });
  if(!open){ el.classList.add('open'); a.classList.add('open'); }
}

// FORM
function submitForm(){
  var name = document.getElementById('f-name').value.trim();
  var email = document.getElementById('f-email').value.trim();
  if(!name || !email){ alert('Vyplňte prosím meno a email.'); return; }
  var btn = document.querySelector('.form-submit');
  var btnText = btn.textContent;
  btn.disabled = true;
  btn.textContent = 'Odosielam...';
  var msgEl = document.getElementById('f-msg');
  var payload = {
    meno: name,
    firma: document.getElementById('f-company').value.trim(),
    email: email,
    telefon: document.getElementById('f-phone').value.trim(),
    web: document.getElementById('f-web').value.trim(),
    sprava: (document.title.split('|')[0].trim()) + ' — ' + (msgEl ? msgEl.value.trim() : ''),
    cas: new Date().toLocaleString('sk-SK')
  };
  fetch('https://api.axiona-group.sk/send.php', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  })
  .then(function(r){ return r.json(); })
  .then(function(){
    document.getElementById('contact-form').style.display = 'none';
    document.getElementById('form-success').style.display = 'block';
    fetch(WEBHOOK, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}).catch(function(){});
  })
  .catch(function(){
    btn.disabled = false;
    btn.textContent = btnText;
    alert('Nastala chyba. Skúste znova alebo napíšte na ' + EMAIL);
  });
}

// COOKIES
function getCookie(name){var v=document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');return v?v[2]:null;}
function setCookie(name,val,days){var d=new Date();d.setTime(d.getTime()+days*24*60*60*1000);document.cookie=name+'='+val+';expires='+d.toUTCString()+';path=/';}
function showBanner(){if(!getCookie('cookie_consent')){setTimeout(function(){var b=document.getElementById('cookie-banner');if(b)b.classList.add('visible');},800);}}
function hideBanner(){var b=document.getElementById('cookie-banner');if(b)b.classList.remove('visible');}
function acceptAllCookies(){setCookie('cookie_consent','all',365);hideBanner();}
function rejectCookies(){setCookie('cookie_consent','necessary',365);hideBanner();}
showBanner();
