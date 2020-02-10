'use strict';

function column_class_from_heading(heading) {
    const remove_illegal = /[^0-9A-Za-zÀ-ÖØ-öø-ÿ_]/g;
    const start_alphanumeric = /^[^a-zA-Za-zÀ-ÖØ-öø-ÿ_]+/g;

    return 'class_' + heading.replace(remove_illegal, '').replace(start_alphanumeric, '');
};

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

            $(td).addClass(column_class_from_heading(columns[index]));
            $(td).data('th', columns[index]);
        });
    });
};
