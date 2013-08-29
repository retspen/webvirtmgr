$.expr[':'].Contains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

$(document).ready(function() {
    var filter_html = [
        '<div class="input-append form-inline pull-right" style="margin-right: 20px;">',
        '<div class="form-group" style="margin-bottom: 25px;">',
        '<input type="text" class="form-control" id="filter_input" />',
        '</div>',
        '<input type="button" class="btn btn-default" id="filter_button" value="Filter" />',
        '<button type="button" class="btn btn-default" id="filter_clear">Clear</button>',
        '</div>'
    ].join('');

    // add html to div as first child
    $('div.row').prepend(filter_html);

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
});
