/* Prepínač svetlý / tmavý motív. Počiatočný motív nastaví inline skript v <head> (bez bliknutia). */
(function(){
  var root=document.documentElement;
  var L={sk:['Tmavý režim','Svetlý režim'],en:['Dark mode','Light mode'],de:['Dunkler Modus','Heller Modus']}[(root.lang||'sk').slice(0,2)]||['Tmavý režim','Svetlý režim'];
  function label(b){var l=root.dataset.theme==='light';b.title=b.ariaLabel=l?L[0]:L[1];}
  document.querySelectorAll('.theme-toggle').forEach(function(b){
    label(b);
    b.addEventListener('click',function(){
      root.dataset.theme=root.dataset.theme==='light'?'dark':'light';
      try{localStorage.setItem('axiona-theme',root.dataset.theme);}catch(e){}
      document.querySelectorAll('.theme-toggle').forEach(label);
    });
  });
})();
