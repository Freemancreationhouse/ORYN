(() => {
  'use strict';
  const ID = 'oryn-pattern-designer-launch';
  let scheduled = false;

  function addLauncher() {
    scheduled = false;
    if (location.pathname !== '/') return;
    if (document.getElementById(ID)) return;

    const buttons = Array.from(document.querySelectorAll('button'));
    const forge = buttons.find((button) => (button.textContent || '').trim().includes('Pattern Forge'));
    if (!forge || !forge.parentElement) return;

    const launcher = document.createElement('button');
    launcher.id = ID;
    launcher.type = 'button';
    launcher.className = forge.className;
    launcher.setAttribute('aria-label', 'Open ORYN Pattern Designer');
    launcher.title = 'Create parametric patterns with ORYN Pattern Designer';
    launcher.innerHTML = '<span class="material-icons-outlined" style="font-size:18px">design_services</span><span class="oryn-pd-label">Pattern Designer</span>';
    if (!document.getElementById('oryn-pattern-designer-launch-style')) {
      const style = document.createElement('style');
      style.id = 'oryn-pattern-designer-launch-style';
      style.textContent = '@media(max-width:640px){#oryn-pattern-designer-launch .oryn-pd-label{display:none}}';
      document.head.appendChild(style);
    }
    launcher.addEventListener('click', () => { window.location.href = '/pattern-designer'; });
    forge.parentElement.insertBefore(launcher, forge);
  }

  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(addLauncher);
  }

  schedule();
  const observer = new MutationObserver(() => { if (!document.getElementById(ID)) schedule(); });
  observer.observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('popstate', schedule);
})();
