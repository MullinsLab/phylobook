
// Notes editor, buttons/listeners, contextmenus etc.
tinymce.init({
    selector: '.notes',
    inline: true,
    placeholder: "Click here to add notes.",
    menubar: false,
    toolbar_location: 'bottom',
    content_style: "p { margin: 0; }",
    save_enablewhendirty: true,
    plugins: [
    'save',
    'link',
    'lists',
    'autolink',
    ],
    color_map: [
        "EFE645", "Yellow",
        "FF0000", "Red",
        "537EFF", "Neon Blue",
        "00CB85", "Green",
        "FFA500", "Orange",
        "E935A1", "Pink",
        "00E3FF", "Light Blue",
        "000000", "Black",
        "808080", "Gray",
        "800080", "Purple",
    ],
    toolbar: [
    'save undo redo | bold italic underline | fontselect fontsizeselect',
    'forecolor backcolor | alignleft aligncenter alignright alignfull | numlist bullist outdent indent'
    ],
    valid_elements: 'p[style],strong,em,span[style],a[href],ul,ol,li',
    valid_styles: {
    '*': 'font-size,font-family,color,text-decoration,text-align,background-color'
    },
    powerpaste_word_import: 'clean',
    powerpaste_html_import: 'clean',
    setup:function(ed) {
        ed.on('change', function(e) {
            setDirtyUnsaved(ed.id);
       });
    },
    //Save button call back function
    save_onsavecallback: function (ed) {
        var content = tinymce.activeEditor.getContent();
        var id = tinymce.activeEditor.id.replace("notes-", "");
        var svg = $("#" + id).find(".svgimage").html();
        var proj = $("#project").val();
        var edId = ed.id;
        // check to see if SVG image exists, so it doesn't get overwritten with 0 bytes
        if ($("#" + id).find(".svgimage").html() && $("#" + id).find(".svgimage").html().length > 0) {
            $.ajax({
            type: "POST",
            headers: { "X-CSRFToken": token },
            url: '/projects/note/update/' + proj + "/" + id,
            data: {
                "notes": content,
                "minval": $("#minval-" + id).val(),
                "maxval": $("#maxval-" + id).val(),
                "colorlowval": $("#colorlowval-" + id).val(),
                "colorhighval": $("#colorhighval-" + id).val(),
                "iscolored": $("#iscolored-" + id).val(),
            },
            success: function() {
                $.ajax({
                    type: "POST",
                    headers: { "X-CSRFToken": token },
                    url: '/projects/svg/update/' + proj + "/" + id,
                    data: { "svg": svg },
                    success: function() {
                        setDirtySaved(edId);
                        //alert( id + " saved successfully." );
                    },
                    error: function (err) {
                        alert( id + " Failed to save!!!  Contact dev team." );
                    }
                });
            },
            error: function (err) {
                alert( id + " Failed to save!!!  Contact dev team." );
            }
        });
        } else {
            alert(id + " is missing an SVG image.  It will not be saved.");
            setDirtyUnsaved(ed.id);
        }
    }
});

function setAllDirtyUnsaved() {
    $('.tree').each(function(i, obj) {
        var noteId = $(this).children(".notes").first().attr("id");
        setDirtyUnsaved(noteId);
    });
}

function setDirtyUnsaved(edId) {
    $("#" + edId).closest(".tree").addClass("editedhighlight");
    tinyMCE.get(edId).setDirty(true);
    var savebtnId = edId.replace("notes", "save");
    $("#" + savebtnId).prop('disabled', false);
    $("#" + savebtnId).removeClass("disabled");
}

function setDirtySaved(edId) {
    tinyMCE.get(edId).setDirty(false);
    var savebtnId = edId.replace("notes", "save");
    $("#" + savebtnId).prop('disabled', true);
    $("#" + savebtnId).addClass("disabled");
    $("#" + edId).closest(".tree").removeClass("editedhighlight");
}

window.addEventListener('beforeunload', function (e) {
    var isDirty = false;
    var dirtyEditors = [];
    for (inst in tinyMCE.editors) {
        let dirty = tinyMCE.editors[inst].isDirty();
        if (dirty) {
            dirtyEditors.push(tinyMCE.editors[inst].id);
            isDirty = true;
        }
    }
    if(isDirty) {
        //following two lines will cause the browser to ask the user if they
        //want to leave. The text of this dialog is controlled by the browser.
        e.preventDefault(); //per the standard
        e.returnValue = ''; //required for Chrome
    }
    //else: user is allowed to leave without a warning dialog
});

function updateProgress(percentage) {
    if(percentage > 100) percentage = 100;
    $('#progressBar').css('width', percentage+'%');
    $('#progressBar').attr('aria-valuenow', percentage);
    $('#progressBar').html(percentage+'%');
}

function saveAll() {
    updateProgress(0);
    var treescount = $('.tree').length;
    var treesdone = 0;
    $('.tree').each(function(i, obj) {
        $("#saveallprog").removeClass("hide");
        var noteId = $(this).children(".notes").first().attr("id");
        var content = tinymce.get(noteId).getContent();
        var id = noteId.replace("notes-", "");
        var svg = $("#" + id).find(".svgimage").html();
        var proj = $("#project").val();
        // check to see if SVG image exists, so it doesn't get overwritten with 0 bytes
        if ($("#" + id).find(".svgimage").html() && $("#" + id).find(".svgimage").html().length > 0) {
            $.ajax({
                type: "POST",
                headers: { "X-CSRFToken": token },
                url: '/projects/note/update/' + proj + "/" + id,
                data: {
                    "notes": content,
                    "minval": $("#minval-" + id).val(),
                    "maxval": $("#maxval-" + id).val(),
                    "colorlowval": $("#colorlowval-" + id).val(),
                    "colorhighval": $("#colorhighval-" + id).val(),
                    "iscolored": $("#iscolored-" + id).val()
                },
                success: function() {
                    $.ajax({
                        type: "POST",
                        headers: { "X-CSRFToken": token },
                        url: '/projects/svg/update/' + proj + "/" + id,
                        data: { "svg": svg },
                        success: function() {
                            setDirtySaved(noteId);
                            treesdone++;
                            updateProgress(Math.round((treesdone/treescount)*100));
                            if (treesdone == treescount) {
                                setTimeout(function() {
                                  $("#saveallprog").addClass("hide");
                                }, 2000);

                            }
                        },
                        error: function (err) {
                            alert( id + " Failed to save!!!  Contact dev team." );
                        }
                    });
                },
                error: function (err) {
                    alert( id + " Failed to save!!!  Contact dev team." );
                }
            });
        } else {
            alert(id + " is missing an SVG image.  It will not be saved.");
            treesdone++;
            updateProgress(Math.round((treesdone/treescount)*100));
            if (treesdone == treescount) {
                setTimeout(function() {
                  $("#saveallprog").addClass("hide");
                }, 2000);
            }
        }
    });

}

$(document).ready(function() {
    $( "#saveall" ).on( "click", function() {
        saveAll();
    });
    $(".save").on("click", function() {
        var btnId = $(this).attr('id');
        var edId = btnId.replace("save", "notes");
        tinyMCE.get(edId).execCommand('mceSave');
    });
    $("#sequencedownloadbutton").on( "click", function(e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            headers: { "X-CSRFToken": token },
            url: '/projects/files/download/extractedfasta/' + projectName + "/" + $("#seqsid").val(),
            data: {
                "seqs": getSelectedExtractColorSeqs(),
                "suffix": $("#suffix").val()
            },
            success: function(result) {
                $("#seqbox").val(result);
            },
            error: function (err) {
                alert( $("#seqsid").val() + " Failed to extract!  Contact dev team." );
            }
        });
    });

    $( ".removesequencecolor" ).on( "click", function() {
        var saveid = $(this).attr('id');
        if (saveid == "removesequencecolor") {
            removeAllSeqnum();
            resetSlider();
        } else {
            var id = saveid.replace("removesequencecolor-", "");
            removeAllSeqnum(id);
            resetSlider(id);
        }
    });
    $( ".sequencecolor" ).on( "click", function() {
        var saveid = $(this).attr('id');
        var textitems;
        if (saveid == "sequencecolor") {
            if (confirm("This will set the sequence number color range for *all* trees.  Do you want to proceed?")) {
                removeAllSeqnum();
                textitems = d3.selectAll('text');
                colorizeSeqnum(textitems);
                var values = $("#slider-range").slider("values");
                $(".min").val($("#min").val());
                $(".minval").val($("#min").val());
                $(".max").val($("#max").val());
                $(".maxval").val($("#max").val());
                $(".slider-range").slider('values',0, values[0]);
                $(".colorlowval").val(values[0]);
                $(".slider-range").slider('values',1, values[1]);
                $(".colorhighval").val(values[1]);
                $(".iscolored").val("true");
                var minColor = pickHex([255, 0, 0], [255, 255, 0], values[ 0 ]/100);
                var maxColor = pickHex([255, 0, 0], [255, 255, 0], values[ 1 ]/100);
                $( ".slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + rgb(minColor[0],minColor[1],minColor[2]) + ", " + rgb(maxColor[0],maxColor[1],maxColor[2]) + ")");
                setAllDirtyUnsaved();
            }
        } else {
            var id = saveid.replace("sequencecolor-", "");
            removeAllSeqnum(id);
            var svg = $("#" + id).find("svg")[0];
            textitems = d3.select(svg).selectAll('text');
            colorizeSeqnum(textitems, id);
            var values = $("#slider-range-" + id).slider("values");
            $("#minval-" + id).val($("#min-" + id).val());
            $("#maxval-" + id).val($("#max-" + id).val());
            $("#colorlowval-" + id).val(values[0]);
            $("#colorhighval-" + id).val(values[1]);
            $("#iscolored-" + id).val("true");
            setDirtyUnsaved("notes-" + id);
        }
    });

    function removeAllSeqnum(id) {
        if (id) {
            var svg = $("#" + id).find("svg")[0];
            d3.select(svg).selectAll(".seqnum").each(function(d, i) {
                d3.select(this).remove();
            });
            setDirtyUnsaved("notes-" + id);
        } else {
            d3.selectAll(".seqnum").each(function(d, i) {
                d3.select(this).remove();
            });
            setAllDirtyUnsaved();
        }
    }

    function resetSlider(id) {
        if (id) {
            $("#minval-" + id).val("");
            $("#maxval-" + id).val("");
            $("#colorlowval-" + id).val("");
            $("#colorhighval-" + id).val("");
            $("#iscolored-" + id).val("false");
            $("#slider-range-" + id).slider('values',0, 1);
            $("#slider-range-" + id).slider('values',1, 100);
            $("#min-" + id).val("2");
            $("#max-" + id).val("50");
        } else {
            $(".minval").val("");
            $(".maxval").val("");
            $(".colorlowval").val("");
            $(".colorhighval").val("");
            $(".iscolored").val("false");
            $(".slider-range").slider('values',0, 1);
            $(".slider-range").slider('values',1, 100);
            $(".min" + id).val("2");
            $(".max" + id).val("50");
        }
    }

    function colorizeSeqnum(textitems, id) {
        var dashId = "";
        if (id) {
            dashId = "-" + id;
        }
        textitems.each(function(d) {
            var label = d3.select(this);
            var min = $("#min" + dashId).val();
            var max = $("#max" + dashId).val();
            var lastunderscore = label.text().lastIndexOf("_");
            var numseqs = parseInt(label.text().substring(label.text().lastIndexOf("_") + 1));
            var labelcolor = [];
            if (numseqs < min || lastunderscore == -1) {
                return;
            } else if (numseqs >= max) {
                var values = $( "#slider-range" + dashId).slider( "values");
                labelcolor = pickHex([255, 0, 0], [255, 255, 0], values[ 1 ]/100);
            } else if (numseqs == min) {
                var values = $( "#slider-range" + dashId).slider( "values");
                labelcolor = pickHex([255, 0, 0], [255, 255, 0], values[ 0 ]/100);
            } else if (numseqs >= min) {
                var incrementweight = 100/(max - min);
                var weight = ((numseqs - min) * incrementweight)/100;
                var values = $( "#slider-range" + dashId).slider( "values");
                var minColor = pickHex([255, 0, 0], [255, 255, 0], values[ 0 ]/100);
                var maxColor = pickHex([255, 0, 0], [255, 255, 0], values[ 1 ]/100);
                var labelcolor = pickHex(maxColor, minColor, weight);
            }

            var currentSelectedTextNode = label.node();
            var svgcanvas = d3.select(currentSelectedTextNode.parentNode);
            var rect = currentSelectedTextNode.getBBox();
            var square = d3.symbol().size("36").type(d3.symbolSquare);

            // if there is a transform, grab the x, y
            if (label.attr("transform") != null) {
                rect.x = label.node().transform.baseVal[0].matrix.e - 2;
                rect.y = label.node().transform.baseVal[0].matrix.f + 2;
            }

            svgcanvas
                .append("path")
                .attr("d", square)
                .attr('class', 'seqnum')
                .attr("transform", "translate(" + (rect.x - 4) + "," + (rect.y + 4) + ")")
                .style('fill', rgb(labelcolor[0],labelcolor[1],labelcolor[2]))
                .style("stroke", rgb(labelcolor[0],labelcolor[1],labelcolor[2]));

        });
    }

    function getColorTextLabels(svg, colorClass) {
        var colorLabels = [];
        svg.selectAll("." + colorClass)
        .each(function() {
            colorLabels.push(this.innerHTML);
        });
        return colorLabels;
    }

    function getSelectedExtractColorSeqs() {
        var selected = $('input[name=color]:checked').val();
        var seqs = selected.replace("extract", "seqs");
        return $("#" + seqs).val();
    }

    function showExtractDialog(svg) {
        $("#seqbox").val("");
        var id = $(svg.node()).closest(".imgparent").attr("id");
        var extractred = getColorTextLabels(svg, "boxred");
        var extractyellow = getColorTextLabels(svg, "boxyellow");
        var extractpink = getColorTextLabels(svg, "boxpink");
        var extractlightblue = getColorTextLabels(svg, "boxlightblue");
        var extractorange = getColorTextLabels(svg, "boxorange");
        var extractneonblue = getColorTextLabels(svg, "boxneonblue");
        var extractgreen = getColorTextLabels(svg, "boxgreen");
        var extractblack = getColorTextLabels(svg, "boxblack");
        var extractgray = getColorTextLabels(svg, "boxgray");
        var extractpurple = getColorTextLabels(svg, "boxpurple");

        $("#seqsid").val(id);
        if (extractred.length === 0) {
            $("#extractred").prop("checked", false);
            $("#extractred").attr("disabled", true);
        } else {
             $("#extractred").attr("disabled", false);
            $("#seqsred").val(extractred.join());
        }
        if (extractyellow.length === 0) {
            $("#extractyellow").prop("checked", false);
            $("#extractyellow").attr("disabled", true);
        } else {
            $("#extractyellow").attr("disabled", false);
            $("#seqsyellow").val(extractyellow.join());
        }
        if (extractpink.length === 0) {
            $("#extractpink").prop("checked", false);
            $("#extractpink").attr("disabled", true);
        } else {
            $("#extractpink").attr("disabled", false);
            $("#seqspink").val(extractpink.join());
        }
        if (extractlightblue.length === 0) {
            $("#extractlightblue").prop("checked", false);
            $("#extractlightblue").attr("disabled", true);
        } else {
            $("#extractlightblue").attr("disabled", false);
            $("#seqslightblue").val(extractlightblue.join());
        }
        if (extractorange.length === 0) {
            $("#extractorange").prop("checked", false);
            $("#extractorange").attr("disabled", true);
        } else {
            $("#extractorange").attr("disabled", false);
            $("#seqsorange").val(extractorange.join());
        }
        if (extractneonblue.length === 0) {
            $("#extractneonblue").prop("checked", false);
            $("#extractneonblue").attr("disabled", true);
        } else {
            $("#extractneonblue").attr("disabled", false);
            $("#seqsneonblue").val(extractneonblue.join());
        }
        if (extractgreen.length === 0) {
            $("#extractgreen").prop("checked", false);
            $("#extractgreen").attr("disabled", true);
        } else {
            $("#extractgreen").attr("disabled", false);
            $("#seqsgreen").val(extractgreen.join());
        }
        if (extractblack.length === 0) {
            $("#extractblack").prop("checked", false);
            $("#extractblack").attr("disabled", true);
        } else {
            $("#extractblack").attr("disabled", false);
            $("#seqsblack").val(extractblack.join());
        }
        if (extractgray.length === 0) {
            $("#extractgray").prop("checked", false);
            $("#extractgray").attr("disabled", true);
        } else {
            $("#extractgray").attr("disabled", false);
            $("#seqsgray").val(extractgray.join());
        }
        if (extractpurple.length === 0) {
            $("#extractpurple").prop("checked", false);
            $("#extractpurple").attr("disabled", true);
        } else {
            $("#extractpurple").attr("disabled", false);
            $("#seqspurple").val(extractpurple.join());
        }

        $('#myModal').modal({show:true});
        //$("#totalSequences").text(sequenceTable.page.info().recordsDisplay.toLocaleString());
        //});
    }

    // hide contextMenu if scroll happens while displayed
    window.onscroll = function() {
        hideContextMenu();
    };

    window.addEventListener("click", (e) => {
        // ? close the menu if the user clicks outside of it
        if (e.target.offsetParent != contextMenu && e.target.offsetParent != contextMenuCircle) {
            hideContextMenu();
        } else if (e.target.offsetParent == contextMenuCircle) {
            var colorText = $(e.target).attr("id");
            var color = getColor(colorText.replace("circle", ""));
            if (colorText == "circleremove" && isCircleSelected) {
                setDirtyUnsaved("notes-" + $(currentSelectedCircle).closest(".imgparent").attr("id"));
                d3.select(currentSelectedCircle).remove();
                hideContextMenu();
                return;
            } else if (isCircleSelected) {
                d3.select(currentSelectedCircle).style("fill", color);
                setDirtyUnsaved("notes-" + $(currentSelectedCircle).closest(".imgparent").attr("id"));
                hideContextMenu();
                return;
            }
            if (colorText != "circleremove") {
                var newcircle = drawCircleMarker(color);
                setDirtyUnsaved("notes-" + $(newcircle.node()).closest(".imgparent").attr("id"));
            }
            hideContextMenu();
        } else if (e.target.offsetParent == contextMenu)  {
            var selectedTexts = d3.select(currentSVG).selectAll(".selectedtext");
            var colorText = $(e.target).attr("id");

            if (selectedTexts.size() > 0) {
                selectedTexts.each(function() {
                    if (colorText == "boxextract") {
                        showExtractDialog(d3.select(this.ownerSVGElement));
                        hideContextMenu();
                        return;
                    }
                    processContextMenuClick(e, this, d3.select(this), colorText);
                });
            } else {
                var currentSelectedTextNode = currentSelectedText.node();
                if (colorText == "boxextract") {
                    showExtractDialog(d3.select(currentSelectedTextNode.ownerSVGElement));
                    hideContextMenu();
                    return;
                }
                processContextMenuClick(e, currentSelectedTextNode, currentSelectedText, colorText);
            }
        }
    });

    window.addEventListener('contextmenu', function(e) {
        if (e.target.tagName.toLowerCase() == 'text') {
            e.preventDefault();
            const { clientX: mouseX, clientY: mouseY } = e;
            normalizePozition(mouseX, mouseY, contextMenu);
            hideContextMenu();
            setTimeout(() => {
              contextMenu.classList.add("visible");
            });
            currentSelectedText = d3.select(e.target);
        } else if (e.target.tagName.toLowerCase() == 'circle') {
            e.preventDefault();
            contextMenu.classList.remove("visible");
            isCircleSelected = true;
            currentSelectedCircle = e.target;
            showContextMenuCircle(e, contextMenuCircle);
        } else if (e.target.tagName.toLowerCase() == 'svg') {
            e.preventDefault();
            contextMenu.classList.remove("visible");
            currentSelectedCircleParent = e.target;
            currentSelectedCircleEvent = e;
            showContextMenuCircle(e, contextMenuCircle);
        } else if (e.target.ownerSVGElement) {
            e.preventDefault();
            currentSelectedCircleParent = e.target.ownerSVGElement;
            currentSelectedCircleEvent = e;
            showContextMenuCircle(e, contextMenuCircle);
        } else if (e.target.classList.contains("item")) {
            e.preventDefault();
        }
    });

    function showContextMenuCircle(e, cMenu) {
        const { clientX: mouseX, clientY: mouseY } = e;
        normalizePozition(mouseX, mouseY, cMenu);
        setTimeout(() => {
          cMenu.classList.add("visible");
        });
    }

    function drawCircleMarker(color) {
        var xy = d3.pointer(currentSelectedCircleEvent, currentSelectedCircleParent);
        return d3.select(currentSelectedCircleParent)
        .append('circle')
        .attr('cx', xy[0])
        .attr('cy', xy[1])
        .attr('r', 3)
        .style('fill', color)
        .call(drag);
    }

    // Define drag beavior
    var drag = d3.drag()
        .on("drag", dragged);

    function dragged(event, d) {
        d3.select(this).attr("cx", event.x).attr("cy", event.y);
    }

    contextMenu = document.getElementById("context-menu");
    contextMenuCircle = document.getElementById("context-menu-circle");
    scope = document.querySelector("body");
});
///////
var contextMenu;
var contextMenuCircle;
var scope;
var currentSVG;
var currentSelectedText = "";
var currentSelectedCircleParent = "";
var currentSelectedCircleEvent = "";
var isCircleSelected = false;
var currentSelectedCircle = "";

const normalizePozition = (mouseX, mouseY, menu) => {
    menuWidth = menu.offsetWidth + 4;
    menuHeight = menu.offsetHeight + 4;

    windowWidth = window.innerWidth;
    windowHeight = window.innerHeight;

    if ( (windowWidth - mouseX) < menuWidth ) {
      menu.style.left = windowWidth - menuWidth + "px";
    } else {
      menu.style.left = mouseX + "px";
    }

    if ( (windowHeight - mouseY) < menuHeight ) {
      menu.style.top = windowHeight - menuHeight + "px";
    } else {
      menu.style.top = mouseY + "px";
    }



    /*
    // ? compute what is the mouse position relative to the container element (scope)
    const {
      left: scopeOffsetX,
      top: scopeOffsetY,
    } = scope.getBoundingClientRect();

    const scopeX = mouseX - scopeOffsetX;
    const scopeY = mouseY - scopeOffsetY;

    // ? check if the element will go out of bounds
    const outOfBoundsOnX =
      scopeX + menu.clientWidth > scope.clientWidth;

    const outOfBoundsOnY =
      scopeY + menu.clientHeight > scope.clientHeight;

    let normalizedX = mouseX;
    let normalizedY = mouseY;

    // ? normalzie on X
    if (outOfBoundsOnX) {
      normalizedX =
        scopeOffsetX + scope.clientWidth - menu.clientWidth;
    }

    // ? normalize on Y
    if (outOfBoundsOnY) {
      normalizedY =
        scopeOffsetY + scope.clientHeight - menu.clientHeight;
    }

    return { normalizedX, normalizedY };
    */
};

function showContextMenu(x, y) {
    normalizePozition(x, y, contextMenu);
    setTimeout(() => {
      contextMenu.classList.add("visible");
    });
}

function hideContextMenu() {
    if (currentSVG) {
        d3.select(currentSVG).selectAll(".selectedtext").classed("selectedtext", false);
    }
    contextMenu.classList.remove("visible");
    contextMenuCircle.classList.remove("visible");
    currentSelectedText = "";
    currentSelectedCircleParent = "";
    currentSelectedCircleEvent = "";
    isCircleSelected = false;
    currentSelectedCircle = "";
}

function processContextMenuClick(e, selectedTextNode, selectedText, colorText) {
    var svgcanvas = d3.select(selectedTextNode.parentNode);
    var rect = selectedTextNode.getBBox();
    var offset = 2; // enlarge rect box 2 px on left & right side
    selectedText.classed("mute", (selectedText.classed("mute") ? false : true));
    var labelText = selectedText.text();

    var existingColoredBox = d3.select("#" + labelText);
    if (colorText == "boxremove") {
        existingColoredBox.remove();
        // remove the class of currentSelectedText
        selectedText.attr("class", null);
        hideContextMenu();
        setDirtyUnsaved("notes-" + $(selectedText.node()).closest(".imgparent").attr("id"));
        return;
    }

    // set the class of currentSelectedText to be colorText
    selectedText.attr("class", colorText);

    var color = getColor(colorText.replace("box", ""));

    // if there is a transform, grab the x, y
    if (selectedText.attr("transform") != null) {
        rect.x = selectedText.node().transform.baseVal[0].matrix.e - 1;
        rect.y = selectedText.node().transform.baseVal[0].matrix.f + 2;
    }

    pathinfo = [
        {x: rect.x-offset, y: rect.y },
        {x: rect.x+offset + rect.width, y: rect.y},
        {x: rect.x+offset + rect.width, y: rect.y + rect.height - 1 },
        {x: rect.x-offset, y: rect.y + rect.height - 1 },
        {x: rect.x-offset, y: rect.y },
    ];

    if (existingColoredBox.node()) {
        existingColoredBox.style("stroke", color);
    } else {
        // Specify the function for generating path data
        var d3line = d3.line()
            .x(function(d){return d.x;})
            .y(function(d){return d.y;})
            .curve(d3.curveLinear);

        // Draw the line
        svgcanvas.append("path")
            .attr("id", labelText)
            .attr("d", d3line(pathinfo))
            .style("stroke-width", 1)
            .style("stroke", color)
            .style("fill", "none");
    }
    setDirtyUnsaved("notes-" + $(selectedText.node()).closest(".imgparent").attr("id"));
    hideContextMenu();
}

function getColor(name) {
    if (name == "red") {
        return "red";
    } else if (name == "yellow") {
        return "#efe645";
    } else if (name == "pink") {
        return "#e935a1";
    } else if (name == "lightblue") {
        return "#00e3ff";
    } else if (name == "orange") {
        return "orange";
    } else if (name == "neonblue") {
        return "#537eff";
    } else if (name == "green") {
        return "#00cb85";
    } else if (name == "black") {
        return "black";
    } else if (name == "gray") {
        return "gray";
    } else if (name == "purple") {
        return "purple";
    }
}

// Slider/colorization functions
$( function() {
    $( "#slider-range" ).slider({
        range: true,
        min: 1,
        max: 100,
        values: [ 1, 100 ],
        create: function( event, ui ) {
            // color between rage sliders
            var markers=$(this).slider('values');
            minColor = pickHex([255, 0, 0], [255, 255, 0], markers[ 0 ]/100);
            maxColor = pickHex([255, 0, 0], [255, 255, 0], markers[ 1 ]/100);
            $( "#slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + rgb(minColor[0],minColor[1],minColor[2]) + ", " + rgb(maxColor[0],maxColor[1],maxColor[2]) + ")");
        },
        slide: function( event, ui ) {
            //$( "#amount" ).val( "$" + ui.values[ 0 ] + " - $" + ui.values[ 1 ] );
            // color between rage sliders
            minColor = pickHex([255, 0, 0], [255, 255, 0], ui.values[ 0 ]/100);
            maxColor = pickHex([255, 0, 0], [255, 255, 0], ui.values[ 1 ]/100);
            $( "#slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + rgb(minColor[0],minColor[1],minColor[2]) + ", " + rgb(maxColor[0],maxColor[1],maxColor[2]) + ")");
        }
    });
});

//