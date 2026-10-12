// Shared controls for the standard generated report. No external dependencies.
const panels = [...document.querySelectorAll('.panel')];
const tabs = [...document.querySelectorAll('.tab')];
let selectedPage = 'both', selectedCategory = 'all';
const matchesPage = node => selectedPage === 'both' || node.dataset.pages.split(' ').includes(selectedPage);
function filterReport() {
  tabs.forEach(tab => {
    tab.disabled = tab.dataset.color !== 'all' && !panels.some(panel => matchesPage(panel) && panel.dataset.color === tab.dataset.color);
    tab.title = tab.disabled ? 'No fixes in this category for this page' : '';
  });
  if (tabs.find(tab => tab.dataset.color === selectedCategory)?.disabled) selectedCategory = 'all';
  tabs.forEach(tab => {
    const active = tab.dataset.color === selectedCategory;
    tab.setAttribute('aria-selected', active);
    tab.tabIndex = active ? 0 : -1;
  });
  panels.forEach(panel => {
    const cards = [...panel.querySelectorAll('.card')];
    cards.forEach(card => card.hidden = !matchesPage(card));
    // A panel with cards but none for this page would look empty: hide it too.
    panel.hidden = !matchesPage(panel) || (selectedCategory !== 'all' && panel.dataset.color !== selectedCategory)
      || (cards.length > 0 && cards.every(card => card.hidden));
    updateProgress(panel);
  });
  document.getElementById('empty').hidden = panels.some(panel => !panel.hidden);
}
// Progress counts only the edits visible under the current page filter; the
// full total is in the progress bar's title.
function updateProgress(panel) {
  const count = panel.querySelector('.count');
  if (!count) return;
  const boxes = [...panel.querySelectorAll('.card')].filter(card => !card.hidden).map(card => card.querySelector('.done input')).filter(Boolean);
  const all = boxes.length, done = boxes.filter(box => box.checked).length;
  const total = panel.querySelectorAll('.done input').length, totalDone = panel.querySelectorAll('.done input:checked').length;
  count.textContent = all && done === all ? 'All done! 🎉' : `${done} / ${all} done`;
  panel.querySelector('.fill').style.width = `${all ? 100 * done / all : 0}%`;
  const track = panel.querySelector('.track');
  track.setAttribute('aria-valuemax', all); track.setAttribute('aria-valuenow', done);
  track.title = all === total ? '' : `${totalDone} / ${total} done across all pages`;
}
document.querySelectorAll('.page-option').forEach(button => button.addEventListener('click', () => {
  selectedPage = button.dataset.page;
  document.querySelectorAll('.page-option').forEach(b => b.setAttribute('aria-pressed', b === button));
  filterReport();
}));
tabs.forEach(tab => {
  tab.addEventListener('click', () => { selectedCategory = tab.dataset.color; filterReport(); });
  tab.addEventListener('keydown', event => {
    const available = tabs.filter(t => !t.disabled), index = available.indexOf(tab);
    const next = {ArrowRight: (index + 1) % available.length, ArrowLeft: (index + available.length - 1) % available.length, Home: 0, End: available.length - 1}[event.key];
    if (next === undefined) return;
    event.preventDefault(); available[next].click(); available[next].focus();
  });
});
filterReport();
function openLinkedIssue() {
  let id = location.hash.slice(1);
  try { id = decodeURIComponent(id); } catch {}
  const panel = id ? document.getElementById(id) : null;
  if (!panel?.classList.contains('panel')) return;
  document.querySelector('[data-page="both"]').click();
  tabs[0].click();
  requestAnimationFrame(() => panel.scrollIntoView({block: 'start'}));
}
openLinkedIssue(); window.addEventListener('hashchange', openLinkedIssue);
let toastTimer;
const toast = document.querySelector('.toast');
document.querySelectorAll('.copy').forEach(button => {
  let resetTimer;
  const label = button.getAttribute('aria-label');
  button.addEventListener('click', async () => {
    const value = button.closest('.field').querySelector('.value');
    let ok = false;
    try { await navigator.clipboard.writeText(button.dataset.copy); ok = true; }
    catch {
      const range = document.createRange(); range.selectNodeContents(value);
      const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
      try { ok = document.execCommand('copy'); } catch {}
      if (ok) selection.removeAllRanges();
    }
    clearTimeout(resetTimer);
    button.classList.toggle('copied', ok); button.textContent = ok ? 'Copied ✓' : 'COPY';
    button.setAttribute('aria-label', ok ? 'Copied: ' + label : label);
    if (ok) resetTimer = setTimeout(() => {
      button.classList.remove('copied'); button.textContent = 'COPY'; button.setAttribute('aria-label', label);
    }, 2500);
    toast.textContent = ok ? 'Copied. Ready to paste!' : 'Press ⌘C or Ctrl+C to copy the selected text.';
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.textContent = '', 2200);
  });
});
document.querySelectorAll('.done input').forEach(box => box.addEventListener('change', () => {
  const card = box.closest('.card'), panel = box.closest('.panel'), marker = card.querySelector('.number');
  card.classList.toggle('complete', box.checked); marker.textContent = box.checked ? '✓' : marker.dataset.marker;
  updateProgress(panel);
}));
const dialog = document.querySelector('dialog'), zoom = document.getElementById('zoom');
document.querySelectorAll('.preview').forEach(button => button.addEventListener('click', () => {
  const image = button.closest('.shot').querySelector('img');
  zoom.src = image.src; zoom.alt = image.alt;
  document.getElementById('zoom-title').textContent = button.closest('.card').querySelector('h3').textContent;
  dialog.showModal();
}));
document.querySelector('.close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  if (event.target !== dialog) return;
  const r = dialog.getBoundingClientRect();
  if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
});
