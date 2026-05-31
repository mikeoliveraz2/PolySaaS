(function () {
    'use strict';

    function toggleUrllistField() {
        var select = document.getElementById('id_executescript');
        var urllistRow = document.querySelector('.field-urllist');
        if (!select || !urllistRow) {
            return;
        }
        var useCustom = !select.value;
        urllistRow.style.display = useCustom ? '' : 'none';
    }

    document.addEventListener('DOMContentLoaded', function () {
        var select = document.getElementById('id_executescript');
        if (!select) {
            return;
        }
        select.addEventListener('change', toggleUrllistField);
        toggleUrllistField();
    });
})();
