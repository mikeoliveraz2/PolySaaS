// THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION
// BINGO: Orchestration Bar + Instruction Embed — commit 8cd810c0
(function () {
    'use strict';

    var DARK_PS_THEMES = ['darkly', 'cyborg', 'slate', 'solar', 'superhero'];
    var PARAM_SAMPLE_URL = '/dose/api/atomic-service-param-sample/';
    var lastSampleService = null;

    function isDarkMode() {
        if (document.body.classList.contains('ps-orch-embed-dark')) {
            return true;
        }
        if (document.documentElement.getAttribute('data-bs-theme') === 'dark') {
            return true;
        }
        var psTheme = document.documentElement.getAttribute('data-ps-theme') || '';
        return DARK_PS_THEMES.indexOf(psTheme) !== -1;
    }

    function getJQuery() {
        return window.jQuery || (window.django && window.django.jQuery);
    }

    function getInstructionForm() {
        return document.getElementById('instruction_form')
            || document.querySelector('form[id$="_form"]');
    }

    function getParametersJsonField() {
        var form = getInstructionForm();
        if (!form) {
            return document.getElementById('id_parameters_json');
        }
        return form.querySelector('#id_parameters_json, textarea[name="parameters_json"], input[name="parameters_json"]');
    }

    function parametersJsonIsEmpty(value) {
        var trimmed = (value || '').trim();
        if (!trimmed) {
            return true;
        }
        if (trimmed === '{}' || trimmed === 'null') {
            return true;
        }
        return false;
    }

    function setParametersJsonText(text) {
        var field = getParametersJsonField();
        if (!field) {
            return false;
        }
        field.value = text;
        field.dispatchEvent(new Event('input', { bubbles: true }));
        field.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }

    function focusParametersJsonField() {
        var field = getParametersJsonField();
        if (field) {
            field.focus();
        }
    }

    function lookupEmbeddedSample(serviceName) {
        var catalog = window.PS_ATOMIC_SERVICE_PARAM_SAMPLES;
        if (!catalog || !serviceName) {
            return null;
        }
        if (Object.prototype.hasOwnProperty.call(catalog, serviceName)) {
            return catalog[serviceName];
        }
        return {
            _service: serviceName,
            note: 'Add parameters_json fields required by ' + serviceName + '.',
        };
    }

    function applySample(serviceName, sample, forceReplace) {
        var field = getParametersJsonField();
        if (!field || !sample) {
            return;
        }
        var current = field.value || '';
        var isSameSampleService = lastSampleService === serviceName;
        var shouldReplace = forceReplace || parametersJsonIsEmpty(current) || isSameSampleService;
        if (!shouldReplace) {
            var overwrite = window.confirm(
                'Replace parameters_json with the sample template for ' + serviceName + '?'
            );
            if (!overwrite) {
                return;
            }
        }
        setParametersJsonText(JSON.stringify(sample, null, 2));
        lastSampleService = serviceName;
        focusParametersJsonField();
    }

    function fetchSample(serviceName) {
        return fetch(PARAM_SAMPLE_URL + '?service=' + encodeURIComponent(serviceName), {
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('sample fetch failed');
                }
                return response.json();
            })
            .then(function (data) {
                if (data && data.status === 'ok' && data.sample) {
                    return data.sample;
                }
                return null;
            });
    }

    function fillParametersJsonForService(serviceName, forceReplace) {
        if (!serviceName) {
            lastSampleService = null;
            return;
        }

        var embedded = lookupEmbeddedSample(serviceName);
        if (embedded) {
            applySample(serviceName, embedded, forceReplace);
            return;
        }

        fetchSample(serviceName)
            .then(function (sample) {
                if (sample) {
                    applySample(serviceName, sample, forceReplace);
                }
            })
            .catch(function () { /* optional API fallback only */ });
    }

    function toggleUrllistField() {
        var select = document.getElementById('id_executescript');
        var urllistRow = document.querySelector('.field-urllist');
        if (!select || !urllistRow) {
            return;
        }
        urllistRow.style.display = !select.value ? '' : 'none';
    }

    function onExecutescriptChange() {
        var select = document.getElementById('id_executescript');
        toggleUrllistField();
        if (!select) {
            return;
        }
        fillParametersJsonForService(select.value, false);
    }

    function bindExecutescriptHandlers(select) {
        if (!select || select.dataset.psAtomicServiceBound === '1') {
            return;
        }
        select.dataset.psAtomicServiceBound = '1';
        select.addEventListener('change', onExecutescriptChange);

        var $ = getJQuery();
        if ($ && $.fn.select2) {
            $(select).off('select2:select.psAtomicService').on('select2:select.psAtomicService', onExecutescriptChange);
        }
    }

    function initInstructionSelect2() {
        var $ = getJQuery();
        if (!$ || !$.fn.select2) {
            return;
        }
        var form = getInstructionForm();
        if (!form) {
            return;
        }
        var dark = isDarkMode();
        $(form).find('select').each(function () {
            var $el = $(this);
            if ($el.hasClass('selectfilter')) {
                return;
            }
            if ($el.hasClass('select2-hidden-accessible')) {
                if (!dark) {
                    return;
                }
                try {
                    $el.select2('destroy');
                } catch (e) { /* ignore */ }
            }
            var opts = { width: '100%' };
            if (dark) {
                opts.dropdownCssClass = 'ps-instruction-select2-dark';
                opts.selectionCssClass = 'ps-instruction-select2-dark';
            }
            try {
                $el.select2(opts);
            } catch (e) { /* ignore */ }
        });
        var select = document.getElementById('id_executescript');
        if (select) {
            bindExecutescriptHandlers(select);
        }
    }

    function maybePrefillOnLoad() {
        var select = document.getElementById('id_executescript');
        var field = getParametersJsonField();
        if (!select || !field || !select.value) {
            return;
        }
        if (parametersJsonIsEmpty(field.value)) {
            fillParametersJsonForService(select.value, true);
        }
    }

    function boot() {
        var select = document.getElementById('id_executescript');
        if (select) {
            bindExecutescriptHandlers(select);
            toggleUrllistField();
        }
        setTimeout(initInstructionSelect2, 50);
        setTimeout(initInstructionSelect2, 300);
        setTimeout(function () {
            initInstructionSelect2();
            maybePrefillOnLoad();
        }, 800);
        setTimeout(maybePrefillOnLoad, 1200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
