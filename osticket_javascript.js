
        $(document).ready(function() {
            $("input:not(.dp):visible:enabled:first").focus();
         });
    

    document.addEventListener('DOMContentLoaded', function() {
        if (undefined === window.getComputedStyle(document.documentElement).backgroundBlendMode) {
            document.getElementById('loginBox').style.backgroundColor = 'white';
        }
    });

    function attemptLoginAjax(e) {
        var objectifyForm = function(formArray) { //serialize data function
            var returnArray = {};
            for (var i = 0; i < formArray.length; i++) {
                returnArray[formArray[i]['name']] = formArray[i]['value'];
            }
            return returnArray;
        };
        if ($.fn.effect) {
            // For some reason, JQuery-UI shake does not considere an element's
            // padding when shaking. Looks like it might be fixed in 1.12.
            // Thanks, https://stackoverflow.com/a/22302374
            var oldEffect = $.fn.effect;
            $.fn.effect = function (effectName) {
                if (effectName === "shake") {
                    var old = $.effects.createWrapper;
                    $.effects.createWrapper = function (element) {
                        var result;
                        var oldCSS = $.fn.css;

                        $.fn.css = function (size) {
                            var _element = this;
                            var hasOwn = Object.prototype.hasOwnProperty;
                            return _element === element && hasOwn.call(size, "width") && hasOwn.call(size, "height") && _element || oldCSS.apply(this, arguments);
                        };

                        result = old.apply(this, arguments);

                        $.fn.css = oldCSS;
                        return result;
                    };
                }
                return oldEffect.apply(this, arguments);
            };
        }
        var form = $(e.target),
            data = objectifyForm(form.serializeArray())
        data.ajax = 1;
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: data,
            cache: false,
            success: function(json) {
                if (!typeof(json) === 'object' || !json.status)
                    return;
                switch (json.status) {
                case 401:
                    if (json && json.redirect)
                        document.location.href = json.redirect;
                    if (json && json.message)
                        $('#login-message').text(json.message)
                    if (json && json.show_reset)
                        $('#reset-link').show()
                    if ($.fn.effect) {
                        $('#loginBox').effect('shake')
                    }
                    // Clear the password field
                    $('#pass').val('').focus();
                    break
                case 302:
                    if (json && json.redirect)
                        document.location.href = json.redirect;
                    break
                }
            },
        });
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return false;
    }
    
onsubmit: attemptLoginAjax(event)
