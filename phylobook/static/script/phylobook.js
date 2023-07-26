// Set up a collator so we can sort by numeric value instead of character value
const collatorNumber = new Intl.Collator(undefined, {  
    numeric: true,
    sensitivity: 'base'
})

let sequenceAnnotators = {}    // A collection of sequenceAnnotator objects, keyed by svgID
let sequenceCountLegend = {}   // A collection of sequence count legends used for saving
let lineages = {}              // Lineage names used for extractions
let treeLineagesCounts = {}    // Get count of lineages used for trees

// Notes editor, buttons/listeners, contextmenus etc.
$(document).ready(function() {
    // Get lineages for extractions
    getLineages();

    // Make color map for the tinymces
    let colorMap = []
    for (let color in annotationColors){
        colorMap.push(annotationColors[color].value, annotationColors[color].name);
    }

    tinymce.init({
        selector: '.notes',
        inline: true,
        placeholder: "Click here to add comments.",
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
        color_map: colorMap,
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
                        saveTree(id);

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
                                console.log(err)
                                alert( id + " Failed to save tree!!!\nContact dev team." + err.responseText);
                            }
                        });
                    },
                    error: function (err) {
                        console.log(err)
                        alert( id + " Failed to save notes!!!  Contact dev team." + err.responseText);
                    }
                });
            } else {
                alert(id + " is missing an SVG image.  It will not be saved.");
                setDirtyUnsaved(ed.id);
            }
        }
    });
});

///////
function showCluster(project, file, id, drawboxes) {
    // Assign box color per clustering info
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
            alert( " Failed to get " + project + "/" + file + ". Contact dev team."  + err.responseText + "(" + err.status + ")");
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
    // gets colors for Clustering

    // https://stackoverflow.com/questions/10014271/generate-random-color-distinguishable-to-humans#answer-20129594
    //const goldenAngle = 180 * (3 - Math.sqrt(5));
    //return `hsl(${key * goldenAngle + 60}, 100%, 75%)`
    
    return {"name": annotationColors[key-1].short, "color": "#"+annotationColors[key-1].value.toLowerCase()};
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
        // var noteId = $(this).children(".notes").first().attr("id");
        let noteId = "notes-"+this.id.replace("tree-", "");
        setDirtyUnsaved(noteId);
    });
}

function setDirtyUnsaved(edId) {
    $("#" + edId).closest(".tree").addClass("editedhighlight");
    tinyMCE.get(edId).setDirty(true);
    var savebtnId = edId.replace("notes", "save");
    $("#" + savebtnId).prop('disabled', false);
    $("#" + savebtnId).removeClass("disabled");

    treeLineagesCounts[edId.replace("notes-", "")].disableSetLineagesButtons();
}

function setDirtySaved(edId) {
    tinyMCE.get(edId).setDirty(false);
    var savebtnId = edId.replace("notes", "save");
    $("#" + savebtnId).prop('disabled', true);
    $("#" + savebtnId).addClass("disabled");
    $("#" + edId).closest(".tree").removeClass("editedhighlight");

    treeLineagesCounts[edId.replace("notes-", "")].enableSetLineagesButtons();

    // treeLineagesCounts[edId.replace("notes-", "")].reloadLineageCounts();
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
        // var noteId = $(this).children(".notes").first().attr("id");
        // var content = tinymce.get(noteId).getContent();
        // var id = noteId.replace("notes-", "");
        let id = this.id.replace("tree-", "");
        let noteId = "notes-" + id;
        let content = tinymce.get(noteId).getContent();
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
                    saveTree(id);

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
                            alert( id + " Failed to save tree in saveall!!!/nContact dev team."  + err.responseText + "(" + err.status + ")");
                        }
                    });
                },
                error: function (err) {
                    alert( id + " Failed to save notes in saveall!!!  Contact dev team."  + err.responseText + "(" + err.status + ")");
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
                alert( $("#seqsid").val() + " Failed to extract!  Contact dev team."  + err.responseText + "(" + err.status + ")");
            }
        });
    });

    $( ".removesequencecolor" ).on( "click", function() {
        var saveid = $(this).attr('id');
        if (saveid == "removesequencecolor") {
            if (confirm("This will remove the sequence number color range for *all* trees.  Do you want to proceed?")) {
                removeAllSeqnum();
                resetSlider();
                
                $(".slider-range").each(function (){
                    if (this.id === "slider-range") {return};
                    clearSequenceCountLegend(this.id.replace("slider-range-", ""));
                });
            };
        } else {
            var id = saveid.replace("removesequencecolor-", "");
            removeAllSeqnum(id);
            resetSlider(id);
            clearSequenceCountLegend(id);
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
                $( ".slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, values[ 0 ], values[ 1 ]) + ")");

                $(".slider-range").each(function (){
                    if (this.id === "slider-range") {return};
                    setSequenceCountLegend(this.id.replace("slider-range-", ""));
                });
                
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

            setSequenceCountLegend(id)
            
            setDirtyUnsaved("notes-" + id);
        }
    });

    function clearSequenceCountLegend(id){
        //  Remove the sequence count legend for the particular tree
        $("#slider-range-legend-container-" + id).addClass("hide");
        if($("#name_colors_by_field_legend_container-" + id).hasClass("hide")){
            $("#legends-" + id).addClass("hide");
        };
    }

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
            $("#slider-range-" + id + " .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, 1, 100) + ")");
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
            $("#slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, 1, 100) + ")");
            $(".min" + id).val("2");
            $(".max" + id).val("50");
        }
    }

    function colorizeSeqnum(textitems, id) {
        // Create boxes based on sequence numbers
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
            var values = $( "#slider-range" + dashId).slider( "values");

            if (numseqs < min || lastunderscore == -1) {
                return;
            } else if (numseqs >= max) {
                labelcolor = pickColorFromGradient(gradientColorsRGB, values[ 1 ])
            } else if (numseqs == min) {
                labelcolor = pickColorFromGradient(gradientColorsRGB, values[ 0 ])
            } else if (numseqs >= min) {
                var incrementweight = 100/(max - min);
                var sequencesWeight = ((numseqs - min) * incrementweight);
                var left = values[0];
                var right = values[1];
                var scaleWeight = (right-left)/100;
                var colorWeight = left+(scaleWeight * sequencesWeight);

                labelcolor = pickColorFromGradient(gradientColorsRGB, colorWeight)
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

        for (let colorKey in annotationColors){
            let color = annotationColors[colorKey].short;
            let extractcolor = getColorTextLabels(svg, "box" + color);

            $("#seqsid").val(id);

            if (extractcolor.length === 0) {
                $("#extract"+color).prop("checked", false);
                $("#extract"+color).attr("disabled", true);
            } else {
                 $("#extract"+color).attr("disabled", false);
                $("#seqs"+color).val(extractcolor.join());
            }
        }

        $('#myModal').modal({show:true});
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
    // Look up a color from the annotationColors list and return the value
    if (name === "remove") {return};
    return "#"+annotationColors.filter(color => color.short == name)[0].value
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
           $( "#slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, markers[ 0 ], markers[ 1 ]) + ")");
            
        },
        slide: function( event, ui ) {
            // color between rage sliders
            $( "#slider-range .ui-slider-range" ).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, ui.values[ 0 ], ui.values[ 1 ]) + ")");
        }
    });
});

//////
//  Stuff for setting text colors
class sequenceAnnotator {
    svgID;                 // The ID of the SVG
    svg;                   // The actual SVG object
    sequenceNames = [];    // An array of names of sequences
    fieldValues = [];      // An array of values derived from sequence names, in the form of field_values[place][value]
    legendData = {};       // A dictionary holding information for the sequence names legend

    constructor(args){
        // args: svgID = the ID of the svg
        this.svgID = args.svgID;
        this.svg = $("#" + args.svgID).find(".svgimage")[0];
        // let svg = $("#" + args.svgID).find(".svgimage")[0];

        this.getSequenceNames();
        this.getFieldValues();
        this.getSequenceLegendSettings();

        this.initializeForm();

        // Register with sequenceAnnotators so this object can always be found
        sequenceAnnotators[this.svgID] = this;
    }

    getSequenceNames(){
        //  Extract the sequence names from the svg and put them into sequenceNames
        
        let caller = this;
        d3.select(this.svg).selectAll("text").each(function (d) {
            caller.sequenceNames.push(d3.select(this).text())
        });
        this.sequenceNames.shift();
    };

    getFieldValues(){
        //  Extract the sequence names from the svg and put them into fieldValues
        for (let name in this.sequenceNames[0].split("_")){
            this.fieldValues.push([]);
        };

        for (let name in this.sequenceNames){
            let fields = this.sequenceNames[name].split("_");

            for (let field in fields){
                if (! this.fieldValues[field].includes(fields[field])){
                    this.fieldValues[field].push(fields[field]);
                };
            };
        };
    };

    initializeForm(){
        // Set up the form to select sequence names to color
        let form = "";

        // Build a form based on the fields in fieldValues
        let buttons = [];

        for (let field_counter in this.fieldValues) {
            let field = this.fieldValues[field_counter];

            if (field.length === 1 || field.length > 10 || (parseInt(field_counter)+1) === this.fieldValues.length){
                form += field[0];
            } else {
                form += "<button type='button' class='btn btn-info btn-sm' " + 
                        "id='sequence_annotator_field_" + this.svgID + "___" + field_counter + "'>" + field[0] + "</button>";
                buttons.push("#sequence_annotator_field_" + this.svgID + "___" + field_counter);
            }
            
            if (parseInt(field_counter)+1 < this.fieldValues.length){
                form += "_"
            }
        };

        $("#sequenceAnnotator_"+this.svgID).html(form);
        
        for (let button in buttons){
            // Attach the doFormField method to the buttons
            let caller=this;

            $("#sequenceAnnotatorContainer_"+this.svgID).removeClass("hide");
            $(buttons[button]).on("click", function() {
                caller.doFormField({field: buttons[button].replace("#sequence_annotator_field_", "").split("___")[1]});
            });
        }
    }

    doFormField(args){
        // Show the form to get information about annotating the sequence
        // Args: field = field index we're working with
        let modal = $("#annotations_modal");
        let modalTitle = $("#annotations_modal_title");
        let modalBody = $("#annotations_modal_body");
        let modalButton = $("#annotations_modal_button");

        let form = "";
    
        form += "<input type='hidden' id='sequence_annotator_svgID' value='" + this.svgID + "'>" +
                "<input type='hidden' id='sequence_annotator_field' value='" + args.field + "'>";

        form += "<table class='table'><thead><tr><th scope='col'>Value</th><th scope='col'>Color</th></tr><tbody>"

        let fields = this.fieldValues[args.field];
        for (let field in fields.sort(collatorNumber.compare)){
            form += "<tr><th scope='row'>" + fields[field] + "</th>";
            form += "<td><select id='sequence_annotator_color___" + fields[field] + "' class='selectpicker' data-width='100px'>" + sequenceColorOptions() + "</select></td></tr>";
        }

        form += "</tbody></table>";

        modalTitle.html("Annotate sequence names for: " + this.sequenceFieldName({field: args.field}));
        modalBody.html(form);
        modalButton.html("Color Sequences");
        
        let caller = this;
        modalButton.off().on("click", function() {
            caller.setSequenceFields();
        });

        $("[id^=sequence_annotator_value]").selectpicker();
        $("[id^=sequence_annotator_color]").selectpicker();

        modal.modal("show");
    }

    sequenceFieldOptions(args){
        // Reuturns the HTML for a options for a specific field
        // Args: field = field index we're working with
        let options = "<option></option>";
        let field = this.fieldValues[args.field];

        for (let value in field.sort(collatorNumber.compare)){
            options += "<option>" + field[value] + "</option>";
        }

        return options;
    }

    sequenceFieldName(args){
        // Returns the prototype sequence name with the field specified hilighted
        // Args: field = field to hilight
        let sequenceName = "";

        for (let field_counter in this.fieldValues) {
            if (field_counter == args.field){
                sequenceName += "<span style='color: red'>" + this.fieldValues[field_counter][0] + "</span>"
            } else {
                sequenceName += this.fieldValues[field_counter][0]
            }

            if (parseInt(field_counter)+1 < this.fieldValues.length){
                sequenceName += "_"
            }
        };

        return sequenceName;
    }

    setSequenceFields(){
        // Get the fields from the form and color the sequences
        let modal = $("#annotations_modal");
        let field = $("#sequence_annotator_field").val();

        let dirty = false;
        let caller = this;

        let settings = {fieldLegend: {
                            field: field,
                            values: [],
                        }
        };

        $("[id^=sequence_annotator_color]").each(function(){
            let value = this.id.split("___")[1];
            let color = $("#sequence_annotator_color___"+value).val();
            
            if (color === "") {return true};

            settings.fieldLegend.values.push({value: value, color: color});
            
            caller.setSequenceNameColorByField({field: field, value: value, color: color});
            dirty = true;
        })

        this.legendData = settings.fieldLegend;
        this.createLegend();

        if (dirty) {setDirtyUnsaved("notes-"+caller.svgID)};
        modal.modal("hide");
    }

    setSequenceNameColorByField(args){
        // Sets sequence names that match the args to a color
        // Args: field = field to match on
        //       value = value to match
        //       color = color to set
        d3.select(this.svg).selectAll("svg text").each(function (d) {
            let fields = d3.select(this).text().split("_");
            if (fields[args.field] == args.value){
                d3.select(this).attr("fill", sequenceAnnotationColors[args.color].value);
            }
        });
    };

    getSequenceLegendSettings(data){
        // Get the fieldLegend setting from the server.  Calls itself on success
        if (! data){
            getTreeSettings({tree: this.svgID, setting: "fieldLegend", callback: jQuery.proxy(this.getSequenceLegendSettings, this)})
        };
        
        this.legendData = data;
        this.createLegend();
    }

    createLegend(){
        // Creates the legend for the sequence name annotations
        if (jQuery.isEmptyObject(this.legendData)){
            return;
        };

        let fieldName = this.sequenceFieldName({field: this.legendData.field});
        $("#name_colors_by_field_legend_field-" + this.svgID).html(fieldName);

        let values = "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        for (let value_index in this.legendData.values){
            let value = this.legendData.values[value_index];
            values += "<b><span style='color: " + sequenceAnnotationColors[value.color].value + "'>" + value.value + "</span></b> &nbsp;";
        }
        $("#name_colors_by_field_legend-" + this.svgID).html(values);

        $("#name_colors_by_field_legend_container-" + this.svgID).removeClass("hide");
        $("#legends-" + this.svgID).removeClass("hide");
    }

    saveLegendData(){
        // Save this.legendData to the db
        setTreeSetting({tree: this.svgID, settings: {fieldLegend: this.legendData}});
    }
};


class treeLineagesCount {
    svgID = "";             // ID of the SVG we're working with
    lineageCounts = {};    // A dictionary holding information for the lineage counts

    constructor(args){
        // args: svgID = the ID of the svg
        this.svgID = args.svgID;

        // this.getLineageCounts();

        // Register with treeLineagesCounts so this object can always be found
        treeLineagesCounts[this.svgID] = this;
    }

    getLineageCounts(args){
        // Get the lineage counts from the server.

        let async = true;
        if (args && args.async === false){
            async = false;
        }

        let recolor = false;
        if (args && args.recolor){
            recolor = true;
        };

        getLineageCounts({tree: this.svgID, func: jQuery.proxy(this.receiveLineageCounts, this), async: async, recolor: recolor});
    }

    receiveLineageCounts(data){
        // Receive the lineage counts from the server.
        this.lineageCounts = data;
        this.enableSetLineagesButtons();
    };

    reloadLineageCounts(){
        // Reload the lineage counts from the server

        this.getLineageCounts();
    };

    enableSetLineagesButtons(){
        // Enable the set lineage names button

        if (Object.keys(lineages).length == 0){
            setTimeout(this.enableSetLineagesButtons.bind(this), 100);
        }
        else {
            $("#set_lineage_names-" + this.svgID).prop("disabled", false);
            $("#set_lineage_names-" + this.svgID).removeClass("disabled");

            $("#extract_to_file-" + this.svgID).prop("disabled", false);
            $("#extract_to_file-" + this.svgID).removeClass("disabled");
        }
    }

    disableSetLineagesButtons(){
        // Disable the set lineage names button
        $("#set_lineage_names-" + this.svgID).prop("disabled", true);
        $("#set_lineage_names-" + this.svgID).addClass("disabled");

        $("#extract_to_file-" + this.svgID).prop("disabled", true);
        $("#extract_to_file-" + this.svgID).addClass("disabled");
    };

    showModalForm(args){
        // Show the form to get information about lineage names
        // Args: download = true if we're downloading the data
        let modal = $("#annotations_modal");
        let modalTitle = $("#annotations_modal_title");
        let modalBody = $("#annotations_modal_body");
        let modalButton = $("#annotations_modal_button");
        let bonusButton = $("#annotations_bonus_button");
        let closeButton = $("#annotations_close_button");

        let download_flag = false;
        if (args && args.download){
            download_flag = true;
        };

        let recolor_flag = false;
        if (args && args.recolor){
            recolor_flag = true;
        };

        let form = "";

        // Get lineage counts using synchronus ajax

        if (recolor_flag) {
            this.getLineageCounts({async: false, recolor: true});
        }
        else if (! download_flag){
            this.getLineageCounts({async: false});
        }

        if ("error" in this.lineageCounts) {
            // Present error message

            form = this.lineageCounts["error"];

            modalButton.html("Assign lineage names");
            modalButton.prop("disabled", true);
            modalButton.addClass("disabled");

            closeButton.removeClass("hide");
            bonusButton.addClass("hide");
        }
        else if (download_flag){
            // Present form to download the file

            form = "Lineage names for this tree have been saved.\nYou can now close this window or download the sequences."
            
            let caller = this;
            modalButton.off().on("click", function() {
                jQuery.proxy(caller.downloadLineagesCallback({close: true}));
            });

            modalButton.html("Download lineages");
            modalButton.prop("disabled", false);
            modalButton.removeClass("disabled");

            closeButton.removeClass("hide");
            bonusButton.addClass("hide");
        }
        else
        {
            // Present form to set lineage names

            if (recolor_flag) {
                loadSVG(this.svgID);
            }

            let totalCount = this.lineageCounts["total"]["count"]

            if (this.lineageCounts["swap_message"] && ! recolor_flag) {
                let script = 'recolorTreeByLineageCounts({id: "' + this.svgID + '", presentModal: true})';

                form += "<div class='container border border-2 rounded warn'><br>This tree has lineages that are miscolored:";
                form += "<br>(" + this.lineageCounts["swap_message"] + ")";
                form += "<div class='d-flex flex-row-reverse'><div class='p-2 bd-highlight'><button type='button' class='btn btn-outline-primary btn-sm mb-2 bg-light' onclick='" + script + "'>Recolor tree by lineage counts</button></div></div>";
                form += "</div><br>";
            }
            else if (this.lineageCounts["swap_message"] && recolor_flag) {
                form += "<div class='container border border-2 rounded success'><br>Lineages have been recolored based on count of sequences at earliest timepoint";
                form += "<br>(" + this.lineageCounts["swap_message"] + ")";
                form += "</div><br>";
            };

            if (this.lineageCounts["warnings"]) {
                for (let warning_index in this.lineageCounts["warnings"]){
                    form += "<div class='container border border-2 rounded warn'><br>";
                    form += this.lineageCounts["warnings"][warning_index];
                    form += "</div><br>";
                };
            };

            form += "<table class='table'><thead><tr><th scope='col'>Color</th><th scope='col'>Lineage Name</th></tr><tbody>"

            for (let color_index in annotationColors) {
                let color = annotationColors[color_index]
                
                form += "<tr><th scope='row'><span  class='" + color["short"] + "_text'>" + color["name"] + "</span>";

                let count_info = {};

                // Create labels for the lineages
                if (color["short"] in this.lineageCounts && this.lineageCounts[color["short"]]["count"]){
                    count_info = this.lineageCounts[color["short"]];

                    form += "<br><span class='lineage_info'>";
                    if (count_info["timepoint"]){
                        form += "<span class='lineage_name'>tp-" + count_info["timepoint"] + "</span>";
                    }
                    
                    form += count_info["count"] + " (" + Math.round((count_info["count"]/totalCount)*1000)/10 + "% of <span class='lineage_name'>total</span>)";
                    form += "</span>";
                }
                else if (color["short"] in this.lineageCounts && this.lineageCounts[color["short"]]["timepoints"]){
                    form += "<br><span class='lineage_info'>";
                    let first = true;

                    for (let timepoint_index in Object.keys(this.lineageCounts[color["short"]]["timepoints"]).sort()){
                        let timepoint = Object.keys(this.lineageCounts[color["short"]]["timepoints"]).sort()[timepoint_index];
                        let timepointTotal = this.lineageCounts["total"]["timepoints"][timepoint];
                        let timepointCount = this.lineageCounts[color["short"]]["timepoints"][timepoint]

                        if (! first){
                            form += "<br>";
                        }

                        form += "<span class='lineage_name'>tp-" + timepoint + "</span>: <b>" + timepointCount + "</b>";
                        form += " (<b>" + Math.round((timepointCount/timepointTotal)*1000)/10 + "%</b> of <span class='lineage_name'>tp-" + timepoint + "</span>, ";
                        form += "" + Math.round((timepointCount/totalCount)*1000)/10 + "% of <span class='lineage_name'>total</span>)";

                        first = false;
                    };

                    form += "</span>";
                };

                form += "</th>";
                
                // Create dropdown for lineage names
                if (lineages[color["name"]].length > 1){
                    form += "<td><select id='lineage___" + color["short"] + "' class='selectpicker' data-width='100px'>";
                    
                    form += "<option value=''>unused</option>";

                    for (let name_index in lineages[color["name"]]){
                        let selected = "";
                        let selecting_name = lineages[color["name"]][name_index];
                        let selecting_default = false;

                        // Special case for Red.  Should be genericized in the future
                        
                        if (color["short"] == "red") {
                            if (selecting_name == "MxL1"){
                                for (let check_color_index in annotationColors) {
                                    let check_color = annotationColors[check_color_index];
                                    if (lineages[check_color["name"]].length == 1) {
                                        if (check_color["short"] in this.lineageCounts) {
                                            selecting_default = true;
                                            break;
                                        };
                                    };
                                };
                            }
                            else if (selecting_name == "SxL"){
                                selecting_default = true;
                                for (let check_color_index in annotationColors) {
                                    let check_color = annotationColors[check_color_index];
                                    if (lineages[check_color["name"]].length == 1) {
                                        if (check_color["short"] in this.lineageCounts) {
                                            selecting_default = false;
                                            break;
                                        };
                                    };
                                };
                            };
                        }
                        else
                        {
                            if (selecting_name.startsWith("*")){
                                selecting_name = selecting_name.replace("*", "");
                                selecting_default = true;
                            };
                        };

                        let current_name = "";

                        if (color["short"] in this.lineageCounts && "name" in this.lineageCounts[color["short"]]){
                            current_name = this.lineageCounts[color["short"]]["name"];
                        };

                        if (current_name == selecting_name){
                            selected = "selected";
                        }
                        else if (selecting_default) {
                            selected = "selected";
                        }
                        else {
                            selected = "";
                        };

                        form += "<option value='" + selecting_name + "' " + selected + ">" + selecting_name + "</option>";
                    };

                    form += "</select></td>";
                }
                else {
                    form += "<td>" + lineages[color["name"]][0] + "</td>";
                };
            };

            form += "</tbody></table>";

            modalButton.html("Assign lineage names");
            modalButton.prop("disabled", false);
            modalButton.removeClass("disabled");

            let caller = this;
            if (args && "download" in args){
                download = args["download"];
            }
            modalButton.off().on("click", function() {
                caller.saveLineageNames();
            });

            closeButton.addClass("hide");
            
            bonusButton.html("Clear lineage assignments")
            bonusButton.removeClass("hide");
            bonusButton.off().on("click", function() {
                caller.clearLineageNames();
            });
        };

        modalTitle.html("Assign lineage names by color for: " + this.svgID);
        if (this.lineageCounts["total"]){
            let timepointAccumulator = "";

            if ("timepoints" in this.lineageCounts["total"]){
                for (let timepoint_index in Object.keys(this.lineageCounts["total"]["timepoints"]).sort()){
                    let timepoint = Object.keys(this.lineageCounts["total"]["timepoints"]).sort()[timepoint_index];
                    // timepointAccumulator += this.lineageCounts["total"]["timepoints"][timepoint] + " @" + timepoint + ", ";
                    timepointAccumulator += "<span class='lineage_name'>tp-" + timepoint + ":</span> " + this.lineageCounts["total"]["timepoints"][timepoint] + ", ";
                };
            };
            
            modalTitle.append("<br><span class='subtitle'>Sequences: " + timepointAccumulator  + " <span class='lineage_name'>total: </span>" + this.lineageCounts["total"]["count"] + "</span>");
        }

        modalBody.html(form);

        $("[id^=lineage___]").selectpicker();

        modal.modal("show");
    };

    saveLineageNames(args){
        // Get the fields from the form and save it to the db
        // args: download = true if we're downloading the data
        let modal = $("#annotations_modal");

        let my_lineages = {};

        for (let color_index in annotationColors){
            let color = annotationColors[color_index]
            let name = $("#lineage___" + color["short"]).find(":selected").val(); // || "";

            if (name === undefined){
                name = lineages[color["name"]][0];
            };

            if (name && Object.values(my_lineages).includes(name)){
                alert("More than one color is assigned to the same lineage name.  Please fix this and try again.");
                return;
            }

            if (name === ""){
                if (color["short"] in this.lineageCounts && (this.lineageCounts[color["short"]]["count"] > 0 || "timepoints" in this.lineageCounts[color["short"]])){
                    alert("You must assign a lineage name to each color that has sequences.");
                    return;
                }
                else {
                    name = undefined;
                };
            }

            my_lineages[color["short"]] = name;
        };

        // Send the data to the server
        setTreeSetting({tree: this.svgID, settings: {lineages: my_lineages}})
        this.showModalForm({download: true});
        this.setLineageNamesAssigned(true);
    };

    clearLineageNames(){
        // Clear the lineage names

        let modal = $("#annotations_modal");
        
        setTreeSetting({tree: this.svgID, settings: {lineages: {}}})
        modal.modal("hide");
        this.setLineageNamesAssigned(false)
    };

    downloadLineagesCallback(args){
        // Download the lineage as a zip

        window.open("/projects/extract_to_zip/" + projectName + "/" + this.svgID,"_self")

        if (args && args.close){
            $("#annotations_modal").modal("hide");
        }
    };

    checkLineageNames(){
        // Check the lineage names to make sure they're all set

        let caller = this;
        $.ajax({
            type: "POST",
            headers: { "X-CSRFToken": token },
            url: '/projects/lineages_ready/' + projectName + "/" + this.svgID,
            success: function(data) {
                caller.setLineageNamesAssigned(data["assigned"])
            },
            error: function (err) {
                console.log(err)
                alert( this.svgID + " Failed to load information on assignment names.\n  Contact dev team." + err.responseText + "(" + err.status + ")");
            }
        });
    }

    setLineageNamesAssigned(assigned) {
        //  Set the lable and color of the lineage names legend

        if (assigned) {
            $("#lineage_names_assigned_tag-" + this.svgID).html("Lineage names assigned");
            $("#lineage_names_assigned_tag-" + this.svgID).addClass("lineage_tag_assigned");
            $("#lineage_names_assigned_tag-" + this.svgID).removeClass("lineage_tag_unassigned");
        }
        else {
            $("#lineage_names_assigned_tag-" + this.svgID).html("Lineage names not assigned");
            $("#lineage_names_assigned_tag-" + this.svgID).addClass("lineage_tag_unassigned");
            $("#lineage_names_assigned_tag-" + this.svgID).removeClass("lineage_tag_assigned");
        }
    }
};


function sequenceColorOptions(){
    // Return an options list with the sequence colors
    let options = "<option></option>";

    for (let color in sequenceAnnotationColors){
        options += "<option value=" + color + "  style='color: " + sequenceAnnotationColors[color].value + ";'>" + sequenceAnnotationColors[color].name + "</option>"
    }

    return options;
}

function setTreeSetting(args){
    // Store a setting dictionary on the server
    // Args: tree = ID of the tree to store the settings for
    //       setting = name of the setting to store

    let callback = function() {}

    if (args.callback) {
        callback = args.callback;
    };

    $.ajax({
        type: "POST",
        headers: { "X-CSRFToken": token },
        url: '/projects/settings/' + projectName + "/" + args.tree,
        data: JSON.stringify(args.settings),
        dataType: 'json',
        success: callback,
        error: function (err) {
            alert( args.tree + " Failed to save settings!!!  Contact dev team." + err.responseText + "(" + err.status + ")");
        }
    });
};

function getTreeSettings(args){
    // Load a setting dictionary from the server
    // Args: tree = ID of the tree to load settings for
    //       setting = name of the setting to load
    //       func = function to call on success
    $.ajax({
        type: "GET",
        headers: { "X-CSRFToken": token },
        url: '/projects/settings/' + projectName + "/" + args.tree + "/" + args.setting,
        data: JSON.stringify(args.settings),
        dataType: 'json',
        success: args.callback,
        error: function (err) {
            console.log(err)
            console.log("Failed to get settings: Tree: " + args.tree + ", Setting: " + args.setting)
        }
    });
}

function setSequenceCountLegend(id, initial){
    // Sets the sequence count legend for the particular tree

    let min = $("#min-" + id).val();
    let max = $("#max-" + id).val();
    let values = $("#slider-range-" + id).slider("values");

    $("#slider-range-legend-" + id).css("background-image", "linear-gradient(to right, " + linearGradient(gradientColorsRGB, values[ 0 ], values[ 1 ]) + ")");
    $("#slider-range-legend-min-" + id).html(min);
    $("#slider-range-legend-max-" + id).html(max);

    $("#slider-range-legend-container-" + id).removeClass("hide");
    $("#legends-" + id).removeClass("hide");
    
    sequenceCountLegend[id] = {clusterLegend: {
                                    min: values[ 0 ],
                                    max: values[ 1 ],
                                    sliderLeft: min,
                                    sliderRight: max,
                                }   
    }

    return;
};

// Move all saving into here to dedupe the code
function saveTree(id){
    // Save everything for the tree
    if (id in sequenceAnnotators) {sequenceAnnotators[id].saveLegendData()};
    if (id in sequenceCountLegend){
        setTreeSetting({tree: id, 
                        settings: sequenceCountLegend[id],
        });     
    };
};


function getLineages(){
    // Get the lineages from the server
    $.ajax({
        type: "GET",
        headers: { "X-CSRFToken": token },
        url: "/projects/lineages",
        dataType: "json",
        success: function(data) {
            lineages = data;
            
            $("[id^=extract_to_file-]").prop('disabled', false);
            $("[id^=extract_to_file-]").removeClass("disabled");
        },
        error: function (err) {
            console.log(err)
            alert( id + " Failed to get lineages!!!  Contact dev team." );
        }
    });
};
 

function getLineageCounts(args){
    // Get lineage counts for a particular tree
    // Args: tree = ID of the tree to load settings for
    //       func = function to call on success

    let async = true;
    if (args && args.async === false) {
        async = false;
    };

    let url = "/projects/lineages/" + projectName + "/" + args.tree
    if (args && args.recolor){
        url = '/projects/lineages/' + projectName + "/" + args.tree + "/recolor";
    }

    $.ajax({
        type: "GET",
        headers: { "X-CSRFToken": token },
        url: url,
        data: JSON.stringify(args.settings),
        dataType: 'json',
        success: args.func,
        async: async,
        error: function (err) {
            // alert( args.tree + " Failed to load lineage counts!!!  Contact dev team." );
            console.log(err)
            console.log("Failed to load lineage counts: Tree: " + args.tree)
        }
    });
};


function setLineagesByColor(id) {
    treeLineagesCounts[id].showModalForm();
};


function downloadLineagesByColor(id) {
    treeLineagesCounts[id].showModalForm();
};


function loadSVG(id){
    // Load the SVG for the tree
    $('#' + id).find(".svgimage").load(projectName + "/" + id, function() {
        // Set up the sequenceAnnotator and the treeLineagesCount after the svg loads
        // console.log("Loaded SVG for " + id);
        
        d3.select($("#" + id).find("svg")[0])
            .call(d3.drag()
                .on("start", function (event, d) {
                    //console.log('start', "x=" + event.x, "y=" + event.y);
                    var xScale = this.width.baseVal.value/this.clientWidth;
                    var yScale = this.height.baseVal.value/this.clientHeight;
                    var datum = {x: event.x * xScale, y: event.y * yScale};
                    rect = d3.select(this).append("rect")
                        .datum(datum)
                        .attr("x", event.x * xScale)
                        .attr("y", event.y * yScale)
                        .attr("height", 0)
                        .attr("width", 0)
                        .attr("class", "selectrect");
                    return false;
                    })
                .on("drag", function (event, d) {
                    var xScale = this.width.baseVal.value/this.clientWidth;
                    var yScale = this.height.baseVal.value/this.clientHeight;
                    var x = rect.datum().x;
                    var y = rect.datum().y;
                    var newx = event.x * xScale;
                    var newy = event.y * yScale;
                    var startx = Math.min(x, newx);
                    var starty = Math.min(y, newy);
                    var width = Math.abs(x - newx);
                    var height = Math.abs(y - newy);
                    rect.attr("x", startx)
                        .attr("y", starty)
                        .attr("width", width)
                        .attr("height", height);

                    //console.log('drag', "x=" + x, "y=" + y, "newx=" + newx, "newy=" + newy, "startx=" + startx, "starty=" + starty, "width=" + width, "height=" + height);
                    })
                .on("end",  function (event, d) {
                    var selectedTexts = getMultiSelectedTexts(this, rect);
                    d3.selectAll(".selectrect").remove();
                    if (selectedTexts.length > 0) {
                        currentSVG = this;
                        showMultiSelectContextMenu(event.sourceEvent.clientX, event.sourceEvent.clientY);
                    }
                    //console.log('end drag');
                    })
            );
    });
};


function recolorTreeByLineageCounts(args) {
    if (args && args["presentModal"]){
        treeLineagesCounts[args.id].showModalForm({recolor: true});
    };
};


function resetTree(id){
    //  Reset the tree to last saved colors

    loadSVG(id);
    setDirtySaved("notes-"+id);
}