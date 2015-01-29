"use strict";
/*
   Copyright (C) 2014 Red Hat, Inc.

   This file is part of spice-html5.

   spice-html5 is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   spice-html5 is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with spice-html5.  If not, see <http://www.gnu.org/licenses/>.
*/

function SpiceFileXferTask(id, file)
{
    this.id = id;
    this.file = file;
}

SpiceFileXferTask.prototype.create_progressbar = function()
{
    var _this = this;
    var cancel = document.createElement("input");
    this.progressbar_container = document.createElement("div");
    this.progressbar = document.createElement("progress");

    cancel.type = 'button';
    cancel.value = 'Cancel';
    cancel.style.float = 'right';
    cancel.onclick = function()
    {
        _this.cancelled = true;
        _this.remove_progressbar();
    };

    this.progressbar.setAttribute('max', this.file.size);
    this.progressbar.setAttribute('value', 0);
    this.progressbar.style.width = '100%';
    this.progressbar.style.margin = '4px auto';
    this.progressbar.style.display = 'inline-block';
    this.progressbar_container.style.width = '90%';
    this.progressbar_container.style.margin = 'auto';
    this.progressbar_container.style.padding = '4px';
    this.progressbar_container.textContent = this.file.name;
    this.progressbar_container.appendChild(cancel);
    this.progressbar_container.appendChild(this.progressbar);
    document.getElementById('spice-xfer-area').appendChild(this.progressbar_container);
}

SpiceFileXferTask.prototype.update_progressbar = function(value)
{
    this.progressbar.setAttribute('value', value);
}

SpiceFileXferTask.prototype.remove_progressbar = function()
{
    if (this.progressbar_container && this.progressbar_container.parentNode)
        this.progressbar_container.parentNode.removeChild(this.progressbar_container);
}

function handle_file_dragover(e)
{
    e.stopPropagation();
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
}

function handle_file_drop(e)
{
    var sc = window.spice_connection;
    var files = e.dataTransfer.files;

    e.stopPropagation();
    e.preventDefault();
    for (var i = files.length - 1; i >= 0; i--)
    {
        if (files[i].type); // do not copy a directory
            sc.file_xfer_start(files[i]);
    }

}
