/* THIS CODE IS FROZEN — NO CHANGES TO THIS CODE ARE ALLOWED WITHOUT THE OWNER'S PERMISSION */
/* BINGO: Unified Endpoint Workspace — 2026-09-01 */

/* Column-driven table renderer shared by every endpoint panel.
 *
 * Replaces the per-object-type table builders. A panel is described by
 * envelope.columns, so adding an object type is a backend change only.
 * Every value goes through esc(), including header labels.
 */
(function (global) {
    'use strict';

    function esc(value) {
        return String(value == null ? '' : value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function money(value) {
        if (value == null || value === '') return '—';
        var num = Number(value);
        if (isNaN(num)) return esc(value);
        return num.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }

    function hasValue(value) {
        return value !== null && value !== undefined && value !== '';
    }

    function columnsFromRows(rows, exclude) {
        var skip = exclude || ['id'];
        var first = null;
        for (var i = 0; i < rows.length; i++) {
            if (rows[i] && typeof rows[i] === 'object') { first = rows[i]; break; }
        }
        if (!first) return [];
        return Object.keys(first)
            .filter(function (key) { return skip.indexOf(key) === -1; })
            .map(function (key) { return {key: key, label: key, format: 'text'}; });
    }

    function cellText(row, column) {
        var raw = row[column.key];
        if (!hasValue(raw) && column.fallback && column.fallback.key) {
            var fallback = row[column.fallback.key];
            if (hasValue(fallback)) {
                return esc((column.fallback.prefix || '') + fallback);
            }
        }
        if (column.format === 'money') return money(raw);
        if (!hasValue(raw)) return esc(column.blank == null ? '—' : column.blank);
        return esc(raw);
    }

    /* Render an envelope into a table. Falls back to deriving columns from the
     * rows when the envelope carries none. */
    function render(envelope, options) {
        var opts = options || {};
        var rows = (envelope && Array.isArray(envelope.rows)) ? envelope.rows : [];
        var columns = (envelope && Array.isArray(envelope.columns) && envelope.columns.length)
            ? envelope.columns
            : columnsFromRows(rows, opts.exclude);
        if (!columns.length) return '';

        var noteClass = opts.noteClass || 'polysaas-callback-dialog__note';
        var head = columns.map(function (column) {
            return '<th>' + esc(column.label || column.key) + '</th>';
        }).join('');

        var body = rows.map(function (row) {
            var cells = columns.map(function (column) {
                var text = cellText(row, column);
                if (column.note_key && row[column.note_key]) {
                    text += '<div class="' + esc(noteClass) + '">' + esc(row[column.note_key]) + '</div>';
                }
                return '<td' + (column.numeric ? ' class="is-num"' : '') + '>' + text + '</td>';
            }).join('');
            return '<tr>' + cells + '</tr>';
        }).join('');

        var table = '<table' + (opts.tableClass ? ' class="' + esc(opts.tableClass) + '"' : '') + '>' +
            '<thead><tr>' + head + '</tr></thead>' +
            '<tbody>' + body + '</tbody></table>';

        return opts.wrapClass ? '<div class="' + esc(opts.wrapClass) + '">' + table + '</div>' : table;
    }

    global.PolySaaSTable = {
        esc: esc,
        money: money,
        render: render,
        columnsFromRows: columnsFromRows
    };
})(window);
