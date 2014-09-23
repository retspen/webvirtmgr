$.expr[':'].Contains = $.expr.createPseudo(function(arg) {
    return function( elem ) {
        return $(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
});

$(document).ready(function() {
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

    $('#hide_vms_bystate input[type=checkbox]').change(function () {
	    $('tbody tr[data-status=' + $(this).data('value') + ']').toggle();
    });
});
