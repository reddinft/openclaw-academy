// OpenClaw Academy — App JS

document.addEventListener('DOMContentLoaded', () => {
  // Add copy buttons to all code blocks
  document.querySelectorAll('pre').forEach(pre => {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.addEventListener('click', () => {
      const code = pre.querySelector('code');
      navigator.clipboard.writeText(code ? code.innerText : pre.innerText)
        .then(() => {
          btn.textContent = 'Copied!';
          setTimeout(() => btn.textContent = 'Copy', 2000);
        });
    });
    pre.style.position = 'relative';
    pre.appendChild(btn);
  });

  // Keyboard navigation
  document.addEventListener('keydown', e => {
    // Only when not in input
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) return;
    
    const prevBtn = document.querySelector('.lesson-nav a:first-child');
    const nextBtn = document.querySelector('.lesson-nav a:last-child');

    if (e.key === 'ArrowLeft' && prevBtn) prevBtn.click();
    if (e.key === 'ArrowRight' && nextBtn) nextBtn.click();
  });
});

// Add copy button styles dynamically
const style = document.createElement('style');
style.textContent = `
  .copy-btn {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(255,255,255,0.1);
    border: none;
    color: #aaa;
    font-size: 0.7rem;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.15s;
  }
  pre:hover .copy-btn { opacity: 1; }
  .copy-btn:hover { background: rgba(255,255,255,0.2); color: #fff; }
`;
document.head.appendChild(style);
