document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('downloadForm');
    const result = document.getElementById('result');
    let currentTaskId = null;
    const submitBtn = document.getElementById('downloadBtn');
    const staticDownloadBtn = document.getElementById('finalDownloadBtnStatic');
    const resetBtn = document.getElementById('resetBtn');

    if (!form || !result) return;

    const getCSRFToken = () => {
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : '';
    };

    const renderStatus = (state) => {
        if (state.error) {
            result.innerHTML = `
        <div class="p-4 rounded-xl bg-red-50 border-2 border-red-200 text-red-700">
          Erreur: ${state.error}
        </div>`;
            enableForm();
            return;
        }

        if (state.status === 'queued') {
            result.innerHTML = `
        <div class="p-4 rounded-xl bg-gray-50 border-2 border-gray-200 text-gray-700">
          En file d'attente...
        </div>`;
            return;
        }

        if (state.status === 'downloading' || state.status === 'processing') {
            const pct = state.progress ?? 0;
            result.innerHTML = `
        <div class="p-4 rounded-xl bg-gray-50 border-2 border-gray-200 text-gray-700">
          <div class="mb-2 flex items-center justify-between">
            <span>${state.status === 'processing' ? 'Traitement...' : 'Téléchargement...'}</span>
            <span>${pct}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div class="bg-[#163e5d] h-3" style="width:${pct}%; transition: width .2s ease"></div>
          </div>
        </div>`;
            return;
        }

        if (state.status === 'finished' && (state.download_url || currentTaskId)) {
            const fname = state.filename || 'media';
            const href = currentTaskId ? `/api/file/${currentTaskId}/` : state.download_url;
            result.innerHTML = `
        <div class=" p-4 rounded-xl bg-gray-50 text-center border-2 border-gray-200 text-green-700">
          Super ! Terminé avec succès 🥳
          <div class="flex flex-wrap justify-center gap-3 mt-4">
            <button type="button" id="finalDownloadBtn" data-href="${href}" class="inline-flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
            </svg>
              Télécharger
            </button>
            <button type="button" id="resetBtnInline" class="inline-flex items-center gap-2 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15">
                </path>
            </svg>
            Réinitialiser</button>
          </div>
        </div>`;
            // Bind dynamic buttons
            const dl = document.getElementById('finalDownloadBtn');
            dl?.addEventListener('click', () => {
                const link = dl.getAttribute('data-href');
                if (link) window.location.href = link;
            });
            const resetInline = document.getElementById('resetBtnInline');
            resetInline?.addEventListener('click', () => doReset());
            enableForm();
            return;
        }

        // fallback
        result.textContent = JSON.stringify(state);
    };

    const pollProgress = (taskId) => {
        currentTaskId = taskId;
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/progress/${taskId}/`);
                const data = await res.json();
                renderStatus(data);
                if (data.status === 'finished' || data.status === 'error') {
                    clearInterval(interval);
                }
            } catch (e) {
                clearInterval(interval);
                renderStatus({ error: 'Erreur de suivi de progression' });
            }
        }, 1000);
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const url = form.querySelector('[name="url"]').value.trim();
        const mediaType = form.querySelector('[name="media_type"]').value;
        const quality = form.querySelector('[name="quality"]').value;

        if (!url) {
            renderStatus({ error: "Veuillez fournir une URL valide" });
            return;
        }

        renderStatus({ status: 'queued' });
        disableForm();

        try {
            const params = new URLSearchParams();
            params.set('url', url);
            params.set('media_type', mediaType);
            params.set('quality', quality);

            const res = await fetch('/api/download/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                },
                body: params.toString(),
            });

            const data = await res.json();
            if (!res.ok) {
                renderStatus({ error: data.error || 'Erreur côté serveur' });
                enableForm();
                return;
            }

            if (data.task_id) {
                pollProgress(data.task_id);
            } else {
                renderStatus({ error: 'Réponse invalide du serveur' });
                enableForm();
            }
        } catch (err) {
            renderStatus({ error: 'Impossible de lancer le téléchargement' });
            enableForm();
        }
    });

    // Select2 init if present
    if (window.jQuery && $.fn.select2) {
        $('#type').select2({ width: '100%', minimumResultsForSearch: Infinity });
        $('#quality').select2({ width: '100%', minimumResultsForSearch: Infinity });
    }

    // Reset handler
    resetBtn?.addEventListener('click', () => doReset());

    // Static download button (server-rendered page)
    staticDownloadBtn?.addEventListener('click', () => {
        const href = staticDownloadBtn.getAttribute('data-href');
        if (href) {
            window.location.href = href;
        }
    });

    function disableForm() {
        submitBtn?.setAttribute('disabled', 'true');
        form.querySelectorAll('input, select').forEach(el => el.setAttribute('disabled', 'true'));
        if (window.jQuery && $.fn.select2) {
            $('#type').prop('disabled', true);
            $('#quality').prop('disabled', true);
        }
    }
    function enableForm() {
        submitBtn?.removeAttribute('disabled');
        form.querySelectorAll('input, select').forEach(el => el.removeAttribute('disabled'));
        if (window.jQuery && $.fn.select2) {
            $('#type').prop('disabled', false);
            $('#quality').prop('disabled', false);
        }
    }
    // Reset routine
    function doReset() {
        currentTaskId = null;
        form.reset();
        if (window.jQuery && $.fn.select2) {
            $('#type').val('video').trigger('change');
            $('#quality').val('best').trigger('change');
        }
        result.innerHTML = '';
        enableForm();
    }
});
