(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const titleInput = document.querySelector('#id_name');  // ← چون فیلد name هست
        const slugInput = document.querySelector('#id_slug');

        if (titleInput && slugInput) {
            titleInput.addEventListener('input', function() {
                let value = titleInput.value.trim();
                const map = {
                    'ا':'a','ب':'b','پ':'p','ت':'t','ث':'s','ج':'j','چ':'ch','ح':'h','خ':'kh','د':'d','ذ':'z',
                    'ر':'r','ز':'z','ژ':'zh','س':'s','ش':'sh','ص':'s','ض':'z','ط':'t','ظ':'z','ع':'a','غ':'gh',
                    'ف':'f','ق':'gh','ک':'k','گ':'g','ل':'l','م':'m','ن':'n','و':'v','ه':'h','ی':'y','ء':'','‌':'-'
                };
                let latin = value.split('').map(ch => map[ch] || ch).join('');
                latin = latin.replace(/\s+/g, '-').replace(/[^a-z0-9\-]/gi, '').toLowerCase();
                slugInput.value = latin;
            });
        }
    });
})();
