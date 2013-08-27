$.expr[':'].Contains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

$(document).ready(function() {
    var filter_html = [
        '<div class="input-append">',
        '<input type="text" id="filter_input" />',
        '<input type="button" class="btn btn-success" id="filter_button" value="Filter" />',
        '<input type="button" class="btn btn-danger" id="filter_clear" value="Clear" />',
        '</div>'
    ].join('');

    // add html to div as first child
    $('div.span8').prepend(filter_html);

    // add event button labeled "filter"
    $('#filter_button').click(function(event) {
        // get value
        var filter_val = $('#filter_input').val();
        if(filter_val == '') {
            // show all
            $('tbody tr').show();
        } else {
            // show only matches
            $('tbody tr:Contains(\'' + filter_val + '\')').show();
            // hide non-matching items
            $('tbody tr:not(:Contains(\'' + filter_val + '\'))').hide();
        }
    });

    // add event button labeled "clear"
    $('#filter_clear').click(function(event) {
        $('#filter_input').val('');
        $('#filter_button').click();
    });

    // trigger filter when enter key pressed
    $('#filter_input').keyup(function(event){
        if(event.keyCode == 13){
            $('#filter_button').click();
        }
    });

    // focus on input field
    $('#filter_input').focus();
});
