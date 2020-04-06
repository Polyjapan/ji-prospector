'use strict';

function getRemoteNiceTable(selector) {
    var url = $(selector).attr('href');
    $.get(url, function(response) {
        $(selector).append(response);
    });
}

class NiceTable {
    constructor (selector, columns) {
        // Is the marker a <remote-nicetable> or not ?
        this.marker = $(selector);
        if (this.marker.attr('href')){
            this.href = this.marker.attr('href');
            this.remote = true;
        } else {
            this.remote = false;
        }

        // Take data from the marker. Hide the marker.
        var rows = $('rows', this.marker); // a bunch of <tr> tags
        var addform = $('add-form', this.marker); // a <form> tag with all due <d> cells inside, and the <input type="submit"> too, already connected to a callback.
        this.columns = columns;
        this.modifiable = (addform.size() != 0);
        this.marker.hide();

        // "Render" the component. Make a table.
        this.marker.after(`<table class="table"></table>`);
        this.table = this.marker.next();
        this.thead = $('<thead></thead>').appendTo(this.table);
        if (this.modifiable){
            var formTbody = $('<tbody></tbody>').appendTo(this.table);
            var formRow = $('<tr></tr>').appendTo(formTbody);
            var showFormRow = $('<tr></tr>').appendTo(formTbody);
        }
        this.rowsTbody = $('<tbody></tbody>').appendTo(this.table);

        // Column titles. Sort logic. Search logic.
        for(const [index, c] of this.columns.entries()){
            if (c == '<search>'){
                // Unnamed, non-sortable column
                var th = $(`<th></th>`).appendTo(this.thead)
                // Add search box
                this.setSearchBox(
                    $('<input class="search form-input" placeholder="Rechercher"/>').appendTo(th)
                );
            } else {
                var th = $(`<th>${c}</th>`).appendTo(this.thead).on(
                    'click', e => { this.sort(index, e); }
                ).append('<small><i class="icon icon-resize-vert"></i></small>');
            }
        }

        // Content rows
        this.setRows(rows.contents());
        rows.remove();

        // Form row, rename tags for cells, hide the form at first
        if (this.modifiable){
            // TODO : find a correct way to give a UUID to every nicetable, because some shit still depends on IDs...
            this.addFormId = 'form_'+(Math.floor(Math.random() * Math.floor(1000000)))

            // Actual form tag, transfer attributes
            var formTag = $('<form></form>').appendTo(this.marker);
            formTag.attr('id', this.addFormId)
            for(const a of ['accept', 'accept-charset', 'action', 'autocomplete', 'enctype', 'method', 'name', 'novalidate', 'target']){
                formTag.attr(a, addform.attr(a));
            }

            // Form row
            formRow.append(addform.contents());
            addform.remove();
            for(const d of $('d', formRow).get()){
                var td = document.createElement('td');
                td.innerHTML = d.innerHTML;
                d.parentNode.replaceChild(td, d);
            }
            $('input, button, textarea, select, label, keygen, output, fieldset', formRow).attr('form', this.addFormId)
            formRow.hide();

            // Show form row
            var td = $('<td />', { colspan:columns.length, columns:'' });
            td = td.appendTo(showFormRow);
            $('<div class="btn btn-sm btn-link col-12"><i class="icon icon-plus"></i></div>').appendTo(td);
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
        // TODO : SET DATA-TH ON EVERY TD ACCORD. TO COLUMNS LIST

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

    refreshRemoteRows (callback) {
        if (this.remote){
            var self = this;
            $.get(this.href, function(response){
                var rows = $(response).find('rows');
                self.setRows(rows.contents());
                callback();
            });
        }
    }

    setSearchBox (collection) {
        this.searchBox = $(collection)
        this.searchBox.on('input', e => {
            this.search(this.searchBox.val());
        });
    }

    sort (columnIndex, event) {
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
            list.sort((a, b) => {return this.sortFunction(a, b, columnIndex);});
        } else {
            list.sort((a, b) => {return this.sortFunction(b, a, columnIndex);});
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
