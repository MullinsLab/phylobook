// Set up a collator so we can sort by numeric value instead of character value
const collatorNumber = new Intl.Collator(undefined, {  
    numeric: true,
    sensitivity: 'base'
})

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
        "FFD8B1", "Apricot",
        "BFEF45", "Lime",
        "808000", "Olive",
        "000075", "Navy",
        "DCBEFF", "Lavender",
        "800000", "Maroon"
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

///////
function showCluster(project, file, id, drawboxes) {
    $.ajax({
        type: "GET",
        headers: { "X-CSRFToken": token },
        url: '/projects/' + project + '/' + file,
        cache: false,
        success: function(csvAsString) {
            clusterArray=csvAsString.csvToArray({ rSep:'\n' });
            var svg = $("#" + id).find("svg")[0];
            //var max = 0;
            var set = new Set();
            for (let i = 0; i < clusterArray.length; i++) {
                var key = clusterArray[i][1];
                set.add(key);
            }
            var uniqueClusters = Array.from(set);
            
            // Sort numerically
            uniqueClusters.sort(collatorNumber.compare);
            var clusterColorKeys = {};
            for (let i = 0; i < uniqueClusters.length; i++) {
                clusterColorKeys[uniqueClusters[i]] = i+1;
            }
            for (let i = 0; i < clusterArray.length; i++) {
                var key = clusterArray[i][1];
                //if (key > max) max = key;
                var classificationColor = getClassficationColor(clusterColorKeys[key]);
                var color = classificationColor["color"];
                var colorText = "box" + classificationColor["name"];
                if (color != "key not found") {
                    var label = d3.select(svg).selectAll("text")
                          .filter(function(){
                            return d3.select(this).text() == clusterArray[i][0];
                          });
                    var currentSelectedTextNode = label.node();
                    var svgcanvas = d3.select(currentSelectedTextNode.parentNode);
                    var rect = currentSelectedTextNode.getBBox();
                    var triangle = d3.symbol().size(12).type(d3.symbolTriangle);

                    // if there is a transform, grab the x, y
                    if (label.attr("transform") != null) {
                        rect.x = label.node().transform.baseVal[0].matrix.e - 2;
                        rect.y = label.node().transform.baseVal[0].matrix.f + 2;
                    }

                    svgcanvas
                        .append("path")
                        .attr("d", triangle)
                        .attr('class', 'cluster')
                        .attr("transform", "translate(" + (rect.x  + rect.width + 5) + "," + (rect.y + 4) + ")")
                        .style('fill', color)
                        .style("stroke", color);

                    if (drawboxes) {
                        var offset = 2; // enlarge rect box 2 px on left & right side
                        var labelText = label.text();
                        var selectedText = label;

                        var existingColoredBox = d3.select("#" + labelText);

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
                    }

                } else {
                    alert(`Not color found for classification #(line ${i}): ${clusterArray[i][1]}`);
                }
            }
            $("#clusterlegend-" + id).html(buildClusterLegend(uniqueClusters, clusterColorKeys));
            setDirtyUnsaved("notes-" + id);
        },
        error: function (err) {
            alert( " Failed to get " + project + "/" + file + ". Contact dev team." );
        }
    });
}

function buildClusterLegend(uniqueClusters, clusterColorKeys) {
    var div = "";
    for (let cluster = 0; cluster < uniqueClusters.length; cluster++) {
        div = div + "<span style='white-space: nowrap;'>" + uniqueClusters[cluster] + "</span>" + "<div class='triangle' + style='border-bottom: 12px solid " + getClassficationColor(clusterColorKeys[uniqueClusters[cluster]])["color"] + " !important;'></div>&nbsp;&nbsp;";
    }
    return div;
}

function getClassficationColor(key) {
    // https://stackoverflow.com/questions/10014271/generate-random-color-distinguishable-to-humans#answer-20129594
    //const goldenAngle = 180 * (3 - Math.sqrt(5));
    //return `hsl(${key * goldenAngle + 60}, 100%, 75%)`
    if (key == "1") {
        return {"name": "red", "color": "red"};
    } else if (key == "2") {
        return {"name": "olive", "color": "olive"};
    } else if (key == "3") {
        return {"name": "neonblue", "color": "#537eff"};
    } else if (key == "4") {
        return {"name": "green", "color": "#00cb85"};
    } else if (key == "5") {
        return {"name": "lavender", "color": "#DCBEFF"};
    } else if (key == "6") {
        return {"name": "maroon", "color": "#800000"};
    } else if (key == "7") {
        return {"name": "orange", "color": "orange"};
    } else if (key == "8") {
        return {"name": "navy", "color": "#000075"};
    } else if (key == "9") {
        return {"name": "lightblue", "color": "#00e3ff"};
    } else if (key == "10") {
        return {"name": "black", "color": "black"};
    } else if (key == "11") {
        return {"name": "lime", "color": "#BFEF45"};
    } else if (key == "12") {
        return {"name": "gray", "color": "gray"};
    } else if (key == "13") {
        return {"name": "apricot", "color": "#FFD8B1"};
    } else if (key == "14") {
        return {"name": "purple", "color": "purple"};
    } else if (key == "15") {
        return {"name": "yellow", "color": "#efe645"};
    } else if (key == "16") {
        return {"name": "pink", "color": "#e935a1"};
    }
}

function getMultiSelectedTexts(svg, rect) {
    hideContextMenu();
    var labels = [];
    var rectbbox = rect.node().getBoundingClientRect();
    var rbx2 = rectbbox.x + rectbbox.width;
    var rby2 = rectbbox.y + rectbbox.height;
    d3.select(svg).selectAll("text")
    .each(function() {
        var textbbox = this.getBoundingClientRect();
        // if there is a transform, grab the x, y
        var selectedItem = d3.select(this);
        if (selectedItem.attr("transform") != null) {
            textbbox.x = this.getScreenCTM().e;
            textbbox.y = this.getScreenCTM().f;
        }
        var tbx2 = textbbox.x + textbbox.width;
        var tby2 = textbbox.y + textbbox.height;
        if (textbbox.x >= rectbbox.x && tbx2 <= rbx2 &&
            textbbox.y >= rectbbox.y && tby2 <= rby2) {
                labels.push(this);
                d3.select(this).classed("selectedtext", true);
            }
    });
    return labels;
}

function showMultiSelectContextMenu(x, y) {
    showContextMenu(x, y);
}

///////

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
        var extractapricot = getColorTextLabels(svg, "boxapricot");
        var extractlime = getColorTextLabels(svg, "boxlime");
        var extractolive = getColorTextLabels(svg, "boxolive");
        var extractnavy = getColorTextLabels(svg, "boxnavy");
        var extractlavender = getColorTextLabels(svg, "boxlavender");
        var extractmaroon = getColorTextLabels(svg, "boxmaroon");

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
        if (extractapricot.length === 0) {
            $("#extractapricot").prop("checked", false);
            $("#extractapricot").attr("disabled", true);
        } else {
            $("#extractapricot").attr("disabled", false);
            $("#seqsapricot").val(extractapricot.join());
        }
        if (extractlime.length === 0) {
            $("#extractlime").prop("checked", false);
            $("#extractlime").attr("disabled", true);
        } else {
            $("#extractlime").attr("disabled", false);
            $("#seqslime").val(extractlime.join());
        }
        if (extractolive.length === 0) {
            $("#extractolive").prop("checked", false);
            $("#extractolive").attr("disabled", true);
        } else {
            $("#extractolive").attr("disabled", false);
            $("#seqsolive").val(extractolive.join());
        }
        if (extractnavy.length === 0) {
            $("#extractnavy").prop("checked", false);
            $("#extractnavy").attr("disabled", true);
        } else {
            $("#extractnavy").attr("disabled", false);
            $("#seqsnavy").val(extractnavy.join());
        }
        if (extractlavender.length === 0) {
            $("#extractlavender").prop("checked", false);
            $("#extractlavender").attr("disabled", true);
        } else {
            $("#extractlavender").attr("disabled", false);
            $("#seqslavender").val(extractlavender.join());
        }
        if (extractmaroon.length === 0) {
            $("#extractmaroon").prop("checked", false);
            $("#extractmaroon").attr("disabled", true);
        } else {
            $("#extractmaroon").attr("disabled", false);
            $("#seqsmaroon").val(extractmaroon.join());
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
    } else if (name == "apricot") {
        return "#FFD8B1";
    } else if (name == "lime") {
        return "#BFEF45";
    } else if (name == "olive") {
        return "#808000";
    } else if (name == "navy") {
        return "#000075";
    } else if (name == "lavender") {
        return "#DCBEFF";
    } else if (name == "maroon") {
        return "#800000";
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