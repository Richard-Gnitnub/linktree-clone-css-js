const statusElement = document.getElementById('share-status');

function announce(message, isError = false) {
  statusElement.textContent = message;
  statusElement.dataset.result = isError ? 'error' : 'ok';
}

async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      // Try the fallback for browsers that block clipboard permissions.
    }
  }

  const field = document.createElement('textarea');
  field.value = text;
  field.setAttribute('readonly', '');
  field.style.position = 'fixed';
  field.style.opacity = '0';
  document.body.appendChild(field);
  field.select();

  let copied = false;
  try {
    copied = document.execCommand('copy');
  } catch {
    copied = false;
  } finally {
    field.remove();
  }
  return copied;
}

document.querySelectorAll('[data-copy]').forEach((button) => {
  button.addEventListener('click', async () => {
    const link = button.closest('.service')?.querySelector('.service-link');
    if (!link) {
      announce('This address is not available.', true);
      return;
    }

    const copied = await copyText(link.href);
    const name = link.querySelector('.service-name')?.textContent.trim() || 'Link';
    announce(
      copied ? name + ' address copied.' : 'Could not copy automatically. Open the link to copy its address.',
      !copied
    );
  });
});

document.getElementById('share-page')?.addEventListener('click', async () => {
  const url = window.location.href;
  if (typeof navigator.share === 'function') {
    try {
      await navigator.share({ title: document.title, url });
      announce('Directory shared.');
      return;
    } catch (error) {
      if (error?.name === 'AbortError') return;
    }
  }

  const copied = await copyText(url);
  announce(
    copied ? 'Directory address copied.' : 'Could not copy automatically. Copy the address from your browser.',
    !copied
  );
});
