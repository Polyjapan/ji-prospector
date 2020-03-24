'use strict';

class NiceTable {
    constructor (selector, columns) {
        // Take data from the component. Hide the component.
        var rows = $('rows', this.marker); // a bunch of <tr> tags // <--- MARKER DEFINED LATER => THIS TAKES ANY <ROWS> IT FINDS, HENCE WHY IT WORKS MDR
        var addform = $('add-form', this.marker); // a <form> tag with all due <td> inside, and the <input type="submit"> too, already connected to a callback.
        this.marker = $(selector);
        this.columns = columns;
        this.modifiable = (addform.size() != 0);
        this.marker.hide();

        // "Render" the component. Make a table.
        this.marker.after(`<table class="table"></table>`);
        this.table = this.marker.next();
        this.thead = $('<thead></thead>').appendTo(this.table);
        this.rowsTbody = $('<tbody></tbody>').appendTo(this.table);
        if (this.modifiable){
            var formTbody = $('<tbody></tbody>').appendTo(this.table);
            var formRow = $('<tr><tr/>').appendTo(formTbody);
            var showFormRow = $('<tr><tr/>').appendTo(formTbody);
        }

        // Column titles. Sort logic. Search logic.
        for(const c of this.columns){
            if (c){
                var th = $(`<th>${c}</th>`).appendTo(this.thead).on(
                    'click', e => { this.sort(c, e); }
                ).append('<small><i class="icon icon-resize-vert"></i></small>');
            } else {
                // Unnamed, non-sortable column
                var th = $(`<th></th>`).appendTo(this.thead)
                // Add search box
                this.searchBox = $('<input class="search form-input" placeholder="Rechercher"/>').appendTo(th);
                this.searchBox.on('input', e => {
                    this.search(this.searchBox.val());
                });
            }
        }

        this.setRows(rows.contents());

        if (this.modifiable){
            // Form row, rename tags for cells, hide the form at first
            formRow.append(addform.contents());
            for(const d of $('d', formRow).get()){
                var td = document.createElement('td');
                td.innerHTML = d.innerHTML;
                d.parentNode.replaceChild(td, d);
            }
            formRow.hide();

            // Show form row
            $('<td />', { colspan:columns.length+1, class:'columns' }).appendTo(showFormRow).append(
                '<div class="btn btn-sm btn-link col-12"><i class="icon icon-plus"></i></div>'
            );
            showFormRow.on('click', e => {
                formRow.show();
                showFormRow.hide();
            });
        }

        // Set default sort function (simple textcontent lexical sort)
        // a and b are rows, simple <tr> Element's.
        // tdIndex gives which <td> should be looked at.
        this.sortFunction = function(a, b, tdIndex) {
            var x = $($(a).children('td').get(tdIndex)).text().toLowerCase();
            var y = $($(b).children('td').get(tdIndex)).text().toLowerCase();
            return x>y;
        };

        // Set default search function (simple textcontent subsequence search)
        this.searchFunction = function(row, searchText) {
            var len = $(row).children('td').filter(function(idx){
                return $(this).text().toUpperCase().includes(searchText.toUpperCase());
            }).size();
            return len != 0;
        };
    }

    setRows (contents) {
        // Add rows, rename tags for rows and cells
        this.rowsTbody.children().remove()
        this.rowsTbody.append(contents);
        for(const d of $('d', this.rowsTbody).get()){
            var td = document.createElement('td');
            td.innerHTML = d.innerHTML;
            d.parentNode.replaceChild(td, d);
        }
        for(const r of $('r', this.rowsTbody).get()){
            var tr = document.createElement('tr');
            tr.innerHTML = r.innerHTML;
            r.parentNode.replaceChild(tr, r);
        }
    }

    sort (column, event) {
        var index = this.columns.indexOf(column);
        var button = $(event.currentTarget);

        // Order toggle logic
        if (!button.attr('order') || button.attr('order') == 'asc'){
            button.attr('order', 'desc');
        } else {
            button.attr('order', 'asc');
        }

        // Sort the list in the right order
        var list = this.rowsTbody.children().get();
        if (button.attr('order') == 'asc'){
            list.sort((a, b) => {return this.sortFunction(a, b, index);});
        } else {
            list.sort((a, b) => {return this.sortFunction(b, a, index);});
        }

        // Replace list
        this.rowsTbody.children().remove();
        this.rowsTbody.append($(list));
    }

    search (text) {
        var searchFunction = this.searchFunction;
        this.rowsTbody.children().show();
        if (text == ''){return;}

        this.rowsTbody.children().not(function(idx){
            return searchFunction($(this), text)
        }).hide();
    }
}
