// ===== Axiona Group — shared site JS =====
var EMAIL   = 'office@axiona-group.sk';
var WEBHOOK = 'https://hook.eu1.make.com/2guic4tnnrc6ci6n3mqmjveaw1vhw1v8';

// JAZYK STRÁNKY (sk / en / de) — texty, ktoré vypisuje JavaScript
var LANG = (document.documentElement.lang || 'sk').slice(0, 2);
if(['sk','en','de'].indexOf(LANG) === -1) LANG = 'sk';
var T = {
  sk: {menuOpen:'Otvoriť menu', menuClose:'Zavrieť menu', name:'meno a priezvisko', company:'názov firmy', email:'platný e-mail',
       phone:'platné telefónne číslo', fill:'Doplňte prosím: ', sending:'Odosielam…', error:'Nastala chyba. Skúste znova alebo napíšte na '},
  en: {menuOpen:'Open menu', menuClose:'Close menu', name:'full name', company:'company name', email:'a valid email',
       phone:'a valid phone number', fill:'Please fill in: ', sending:'Sending…', error:'Something went wrong. Please try again or email us at '},
  de: {menuOpen:'Menü öffnen', menuClose:'Menü schließen', name:'Vor- und Nachname', company:'Firmenname', email:'eine gültige E-Mail-Adresse',
       phone:'eine gültige Telefonnummer', fill:'Bitte ergänzen Sie: ', sending:'Wird gesendet …', error:'Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut oder schreiben Sie an '}
}[LANG];

document.addEventListener('DOMContentLoaded', function(){
  var cel = document.getElementById('contact-email-link');
  if(cel){ cel.href = 'mailto:' + EMAIL; cel.textContent = EMAIL; }
});

function scroll2(id){ var el = document.getElementById(id); if(el) el.scrollIntoView({behavior:'smooth'}); }

// MOBILE NAV (hamburger do 1150 px)
function setNav(open){
  var n = document.querySelector('.nav-links'), b = document.querySelector('.nav-toggle');
  if(!n) return;
  n.classList.toggle('open', open);
  if(b){ b.setAttribute('aria-expanded', open ? 'true' : 'false'); b.setAttribute('aria-label', open ? T.menuClose : T.menuOpen); }
}
function toggleNav(){
  var n = document.querySelector('.nav-links'); if(!n) return;
  var open = !n.classList.contains('open');
  setNav(open);
  // odkazy sú v DOM pred tlačidlom — fokus na prvý odkaz, aby Tab pokračoval v menu
  if(open){ var a = n.querySelector('a'); if(a) setTimeout(function(){ a.focus({preventScroll:true}); }, 30); }
}
function closeNav(){ setNav(false); }
document.addEventListener('DOMContentLoaded', function(){
  var n = document.querySelector('.nav-links'), b = document.querySelector('.nav-toggle');
  if(n && b){
    if(!n.id) n.id = 'nav-menu';
    b.setAttribute('aria-controls', n.id);
    b.setAttribute('aria-expanded', 'false');
  }
  document.querySelectorAll('.nav-links a').forEach(function(a){ a.addEventListener('click', closeNav); });
});
document.addEventListener('keydown', function(e){
  var n = document.querySelector('.nav-links.open');
  if(n && (e.key === 'Escape' || e.key === 'Esc')){ closeNav(); var b = document.querySelector('.nav-toggle'); if(b) b.focus(); }
});
document.addEventListener('click', function(e){
  var n = document.querySelector('.nav-links.open');
  if(n && !e.target.closest('nav')) closeNav();
});



// VALIDÁCIA KONTAKTU — každý dopyt musí mať meno a priezvisko, firmu, e-mail a telefón
function validateLead(d){
  var err = [];
  var parts = (d.meno||'').trim().split(/\s+/).filter(function(p){ return p.replace(/[^A-Za-zÀ-ſ]/g,'').length >= 2; });
  if(parts.length < 2) err.push('meno a priezvisko');
  if((d.firma||'').trim().length < 2) err.push('názov firmy');
  if(!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test((d.email||'').trim())) err.push('platný e-mail');
  var ph = (d.telefon||'').trim();
  if(!/^[+0-9 ()\/-]+$/.test(ph) || ph.replace(/\D/g,'').length < 9) err.push('platné telefónne číslo');
  return err;
}
function markInvalid(ids, bad){
  ids.forEach(function(id){ var el = document.getElementById(id); if(el) el.style.borderColor = ''; });
  bad.forEach(function(id){ var el = document.getElementById(id); if(el) el.style.borderColor = '#d9534f'; });
}

// FORM
function submitForm(){
  var d = {
    meno: document.getElementById('f-name').value.trim(),
    firma: document.getElementById('f-company').value.trim(),
    email: document.getElementById('f-email').value.trim(),
    telefon: document.getElementById('f-phone').value.trim()
  };
  var err = validateLead(d);
  // validateLead vracia slovenské kľúče (používa ich aj /reality/) — tu sa preložia do jazyka stránky
  var map = {'meno a priezvisko':'f-name','názov firmy':'f-company','platný e-mail':'f-email','platné telefónne číslo':'f-phone'};
  var key = {'meno a priezvisko':'name','názov firmy':'company','platný e-mail':'email','platné telefónne číslo':'phone'};
  markInvalid(['f-name','f-company','f-email','f-phone'], err.map(function(e){ return map[e]; }));
  if(err.length){ alert(T.fill + err.map(function(e){ return T[key[e]]; }).join(', ') + '.'); return; }
  // Honeypot: vyplnené skryté pole = robot → nič neodoslať, ale zobraziť bežné potvrdenie
  var hp = document.getElementById('f-company-website');
  if(hp && hp.value.trim()){
    document.getElementById('contact-form').style.display = 'none';
    document.getElementById('form-success').style.display = 'block';
    return;
  }
  var name = d.meno, email = d.email;
  var btn = document.querySelector('.form-submit');
  var btnText = btn.textContent;
  btn.disabled = true;
  btn.textContent = T.sending;
  var msgEl = document.getElementById('f-msg');
  var payload = {
    zdroj: 'Web' + (LANG === 'sk' ? '' : ' ' + LANG.toUpperCase()) + ' – ' + document.title.split('|')[0].trim(),
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
    alert(T.error + EMAIL);
  });
}

// COOKIES
function getCookie(name){var v=document.cookie.match('(^|;) ?'+name+'=([^;]*)(;|$)');return v?v[2]:null;}
function setCookie(name,val,days){var d=new Date();d.setTime(d.getTime()+days*24*60*60*1000);document.cookie=name+'='+val+';expires='+d.toUTCString()+';path=/';}
function showBanner(){if(!getCookie('cookie_consent')){setTimeout(function(){var b=document.getElementById('cookie-banner');if(b)b.classList.add('visible');},800);}}
function hideBanner(){var b=document.getElementById('cookie-banner');if(b)b.classList.remove('visible');}
function setAnalyticsConsent(granted){
  // GA sa načíta až po súhlase (basic consent mode); pri odmietnutí sa nenačíta vôbec
  if(granted && typeof window.axionaLoadGA === 'function') window.axionaLoadGA();
  if(typeof window.gtag === 'function') window.gtag('consent', 'update', {analytics_storage: granted ? 'granted' : 'denied'});
  if(!granted){
    // pri odmietnutí zmazať prípadné staršie GA cookies (_ga, _ga_*, _gid)
    document.cookie.split(';').forEach(function(c){
      var n = c.split('=')[0].trim();
      if(/^_ga($|_)|^_gid$/.test(n)){
        var host = location.hostname.split('.');
        var domains = ['', location.hostname];
        if(host.length > 1) domains.push('.' + host.slice(-2).join('.'));
        domains.forEach(function(d){ document.cookie = n + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/' + (d ? ';domain=' + d : ''); });
      }
    });
  }
}
function acceptAllCookies(){setCookie('cookie_consent','all',365);setAnalyticsConsent(true);hideBanner();}
function rejectCookies(){setCookie('cookie_consent','necessary',365);setAnalyticsConsent(false);hideBanner();}
showBanner();

// PONUKA JAZYKA PODĽA PREHLIADAČA — len ponuka, nikdy automatické presmerovanie (Google, zdieľané odkazy)
(function(){
  var alt = {};
  document.querySelectorAll('link[rel="alternate"][hreflang]').forEach(function(l){ alt[l.hreflang] = l.href; });
  if(!alt.sk) return;
  var pref = ((navigator.languages && navigator.languages[0]) || navigator.language || '').slice(0, 2).toLowerCase();
  if(pref === 'cs') pref = 'sk';
  var target = alt[pref] ? pref : (LANG === 'sk' && pref && pref !== 'sk' ? 'en' : null);
  if(!target || target === LANG || !alt[target]) return;
  try { if(localStorage.getItem('axiona-lang-hint') === LANG) return; } catch(e) {}
  var txt = {sk:['Táto stránka je aj po slovensky','Prejsť →','Zavrieť'], en:['This page is also available in English','Switch →','Close'],
             de:['Diese Seite gibt es auch auf Deutsch','Wechseln →','Schließen']}[target];
  function show(){
    var d = document.createElement('div');
    d.className = 'lang-hint'; d.setAttribute('role', 'status'); d.lang = target;
    d.innerHTML = '<span></span><a></a><button type="button">×</button>';
    d.querySelector('button').setAttribute('aria-label', txt[2]);
    d.firstChild.textContent = txt[0];
    var a = d.querySelector('a'); a.href = alt[target]; a.hreflang = target; a.textContent = txt[1];
    d.querySelector('button').addEventListener('click', function(){
      try { localStorage.setItem('axiona-lang-hint', LANG); } catch(e) {}
      d.remove();
    });
    document.body.appendChild(d);
  }
  // nezakrývať cookie lištu: ukázať až po jej zavretí
  if(getCookie('cookie_consent')) setTimeout(show, 1200);
  else { var h = hideBanner; hideBanner = function(){ h(); setTimeout(show, 400); }; }
})();
