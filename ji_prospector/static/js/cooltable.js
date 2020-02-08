'use strict';

function coolrows(table_id, columns) {
    // Populates a cooltable's <td> tags with the right class and data-th
    // Assumes zepto returns the <td> tags in order ! Otherwise there is nothing we can do...
    var rows = $('#'+table_id+' tr');
    rows.each((index, row) => {
        var items = $(row).children();
        // Avoid header rows
        if(!items.first().is('td')){return;}

        items.each((index, td) => {
            if(index>=columns.length){return;}

            $(td).addClass(columns[index][1]);
            $(td).data('th', columns[index][0]);
        });
    });
};
