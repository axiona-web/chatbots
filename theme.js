/* Prepínač svetlý / tmavý motív. Počiatočný motív nastaví inline skript v <head> (bez bliknutia). */
(function(){
  var root=document.documentElement;
  function label(b){var l=root.dataset.theme==='light';b.title=b.ariaLabel=l?'Tmavý režim':'Svetlý režim';}
  document.querySelectorAll('.theme-toggle').forEach(function(b){
    label(b);
    b.addEventListener('click',function(){
      root.dataset.theme=root.dataset.theme==='light'?'dark':'light';
      try{localStorage.setItem('axiona-theme',root.dataset.theme);}catch(e){}
      document.querySelectorAll('.theme-toggle').forEach(label);
    });
  });
})();
