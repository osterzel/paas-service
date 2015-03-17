(function($){
    var timer;
    var form = $('#searchForm');
    var inputSearch = $("input[name='search']");

    inputSearch.keyup(function() {
        clearTimeout(timer);
        timer = setTimeout(function() { form.submit(); }, 300);
    });

    inputSearch.focus();
    inputSearch.val(inputSearch.val());
})(jQuery);