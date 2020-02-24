'use strict';

function column_class_from_heading(heading) {
    const remove_illegal = /[^0-9A-Za-zÀ-ÖØ-öø-ÿ_]/g;
    const start_alphanumeric = /^[^a-zA-Za-zÀ-ÖØ-öø-ÿ_]+/g;

    return 'class_' + heading.replace(remove_illegal, '').replace(start_alphanumeric, '');
};

function cooltables() {
    // Adds functionality to every cooltable in the document.
    var tables = $('.cooltable');
    tables.each((index, table) => {
        var modifiable = $(table).hasClass('cooltable_modifiable') != null;
        var cols = $.parseJSON($('#columns_json', table).get(0).textContent);
        coolrows(table, cols, modifiable);

        $(table).attr('id', 'cooltable_'+index);
        var tasksList = new List($(table).attr('id'), {valueNames: cols.map( column_class_from_heading )});

        if(modifiable){
            $('.cooltable_show_add_row .btn', table).on('click', e => {
                $('.cooltable_show_add_row', table).attr('hidden', true);
                $('.cooltable_add_row', table).removeAttr('hidden');
            });
        }
    });
}

function coolrows(table, columns, modifiable) {
    // Populates a cooltable's <td> tags with the right class and data-th
    // Assumes zepto returns the <td> tags in order ! Otherwise there is nothing we can do...
    var rows = $('tr', $(table));
    rows.each((index, row) => {
        var items = $(row).children();
        // Avoid header rows
        if(!items.first().is('td')){return;}
        if($(row).hasClass('cooltable_nosort')){return;}

        items.each((index, td) => {
            if(index>=columns.length){
                // First non-named column, which usually contains buttons
                // If the table is modifiable, add an "edit" button and a "remove" button.
                if(modifiable){
                    // TODO
                }
                return;
            }

            $(td).addClass(column_class_from_heading(columns[index]));
            $(td).data('th', columns[index]);
        });
    });
};

cooltables();
