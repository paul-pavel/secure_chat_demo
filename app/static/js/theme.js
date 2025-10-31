(function(){
  const key = 'scd-theme';
  const html = document.documentElement;
  const saved = localStorage.getItem(key);
  if (saved) html.setAttribute('data-theme', saved);
  const btn = document.getElementById('themeToggle');
  if (btn) btn.addEventListener('click', () => {
    const cur = html.getAttribute('data-theme') || 'light';
    const next = cur === 'light' ? 'dark' : 'light';
    html.setAttribute('data-theme', next);
    localStorage.setItem(key, next);
  });
})();
