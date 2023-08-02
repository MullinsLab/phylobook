// Globals
let lineages = {}              // Lineage names used for extractions
let treeLineagesCounts = {}    // Get count of lineages used for trees

function showhideColorRange(id, tag) {
    var text = tag.innerHTML;
    if (text.startsWith("Show")) {
        tag.innerHTML = "Hide annotation tools";
        $("#" + id).removeClass("hide");
    } else {
        tag.innerHTML = "Show annotation tools";
        $("#" + id).addClass("hide");
    }
}

function resizeHighlighterWidth(imgparentid, adjustment) {
    var imgheight = $('#' + imgparentid).find('img').prop("naturalHeight");
    var imgwidth = $('#' + imgparentid).find('img').prop("naturalWidth");
    var curwidth = $('#' + imgparentid).find('img').prop("width");
    var imgratio = imgwidth/imgheight;
    var imgimagewidth = adjustment * imgratio;
    $('#' + imgparentid).find('.highlighter').width(imgimagewidth);

    // adjust highlighter straightedge
    var newOffsetFactor = imgimagewidth/curwidth;
    var elmnt = $('#' + imgparentid).find(".straightedge")[0];
    var newX = elmnt.offsetLeft * newOffsetFactor;
    elmnt.style.left = newX + "px";
}

function resizeSVGWidth(imgparentid, adjustment) {
    var svgheight = $('#' + imgparentid).find('svg').attr('height');
    var svgwidth = $('#' + imgparentid).find('svg').attr('width');
    var svgratio = svgwidth/svgheight;
    var svgimagewidth = adjustment * svgratio;
    $('#' + imgparentid).find('.svgimage').width(svgimagewidth);
}

$(document).ready(function() {
    // Get lineages for extractions
    getLineages();

    $( ".fullsize" ).on( "click", function() {
        var imgparentid = $(this).attr('id').replace("full-", "");
        var svgoriginalheight = $('#' + imgparentid).find('svg').attr('height');
        $('#' + imgparentid).height(svgoriginalheight);
        resizeSVGWidth(imgparentid, svgoriginalheight);
        resizeHighlighterWidth(imgparentid, svgoriginalheight);
    });
    $( ".minsize" ).on( "click", function() {
        var imgparentid = $(this).attr('id').replace("minsize-", "");
        var minheight = 200;
        $('#' + imgparentid).height(minheight);
        resizeSVGWidth(imgparentid, minheight);
        resizeHighlighterWidth(imgparentid, minheight);
    });
    $( ".zoomin" ).on( "click", function() {
        var imgparentid = $(this).attr('id').replace("zin-", "");
        var currentheight = $('#' + imgparentid).height();
        var increase = currentheight * 1.1;
        resizeSVGWidth(imgparentid, increase);
        resizeHighlighterWidth(imgparentid, increase);
        $('#' + imgparentid).height(increase);
    });
    $( ".zoomout" ).on( "click", function() {
        var imgparentid = $(this).attr('id').replace("zout-", "");
        var currentheight = $('#' + imgparentid).height();
        var decrease = currentheight * .9;

        var svgheight = $('#' + imgparentid).find('svg').attr('height');
        var svgwidth = $('#' + imgparentid).find('svg').attr('width');
        var svgratio = svgwidth/svgheight;
        var svgimagewidth = decrease * svgratio;
        $('#' + imgparentid).find('.svgimage').width(svgimagewidth);
        resizeSVGWidth(imgparentid, decrease);
        resizeHighlighterWidth(imgparentid, decrease);
        $('#' + imgparentid).height(decrease);
    });
    $("#downloadproject").click(function() {
        // disable button
        $(this).prop("disabled", true);
        // add spinner to button
        $(this).html(
        `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Downloading...`
        );
        var downloadBtn = $(this);
        var xhr = new XMLHttpRequest();
        xhr.open('GET', '/projects/files/download/' + projectName, true);
        xhr.responseType = 'arraybuffer';

        xhr.onload = function(e) {
            if (this.status == 200) {
                // check for a filename
                var filename = "";
                var disposition = xhr.getResponseHeader('Content-Disposition');
                if (disposition && disposition.indexOf('attachment') !== -1) {
                    var filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    var matches = filenameRegex.exec(disposition);
                    if (matches !== null && matches[1]) filename = matches[1].replace(/['"]/g, '');
                }

                var type = xhr.getResponseHeader('Content-Type');
                console.log("type", type);
                var blob = new Blob([xhr.response], { type: type });

                if (typeof window.navigator.msSaveBlob !== 'undefined') {
                    // IE workaround for "HTML7007: One or more blob URLs were revoked by closing the blob for which they were created. These URLs will no longer resolve as the data backing the URL has been freed."
                    window.navigator.msSaveBlob(blob, filename);
                } else {
                    var URL = window.URL || window.webkitURL;
                    var downloadUrl = URL.createObjectURL(blob);

                    if (filename) {
                        // use HTML5 a[download] attribute to specify filename
                        var a = document.createElement("a");
                        // safari doesn't support this yet
                        if (typeof a.download === 'undefined') {
                            window.location.href = downloadUrl;
                        } else {
                            a.href = downloadUrl;
                            a.download = filename;
                            document.body.appendChild(a);
                            a.click();
                        }
                    } else {
                        window.location.href = downloadUrl;
                    }

                    setTimeout(function () { URL.revokeObjectURL(downloadUrl); }, 200); // cleanup
                    downloadBtn.prop("disabled", false);
                    downloadBtn.html('Download Project Files');
                }
            }
        };
        xhr.onerror = function () {
            downloadBtn.prop("disabled", false);
            downloadBtn.html('Download Project Files');
            alert("Download failed!");
        };
        xhr.send();
    });
});


class treeLineagesCount {
    svgID = "";             // ID of the SVG we're working with
    lineageCounts = {};     // A dictionary holding information for the lineage counts
    downloadOnly = false;   // If true, only allow downloading of the lineages, not assigning

    constructor(args){
        // args: svgID = the ID of the svg
        this.svgID = args.svgID;
        
        if ("downloadOnly" in args){
            this.downloadOnly = args.downloadOnly;
        }

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
        else if (download_flag || this.downloadOnly){
            // Present form to download the file

            if (this.lineageCounts["swap_message"] && ! recolor_flag) {
                form += "<div class='container border border-2 rounded warn'><br>This tree has lineages that are miscolored:";
                form += "<br>(" + this.lineageCounts["swap_message"] + ")";
            }

            if (this.lineageCounts["warnings"]) {
                for (let warning_index in this.lineageCounts["warnings"]){
                    form += "<div class='container border border-2 rounded warn'><br>";
                    form += this.lineageCounts["warnings"][warning_index];
                    form += "</div><br>";
                };
            };

            console.log(this.lineageCounts);

            if (! this.lineageOK()) {
                form += "<div class='container border border-2 rounded warn'><br>";
                form += "Some lineages have not been assigned names.";
                form += "</div><br>";

                modalButton.html("Download lineages");
                modalButton.prop("disabled", true);
                modalButton.addClass("disabled");

                closeButton.removeClass("hide");
                bonusButton.addClass("hide");
            }
            else {
                if (download_flag) {
                    form += "Lineage names for this tree have been saved.\nYou can now close this window or download the sequences."
                }
                else if (this.downloadOnly) {
                    form += "Lineages are ready to download."
                }
            
                let caller = this;
                modalButton.off().on("click", function() {
                    jQuery.proxy(caller.downloadLineagesCallback({close: true}));
                });

                modalButton.html("Download lineages");
                modalButton.prop("disabled", false);
                modalButton.removeClass("disabled");

                closeButton.removeClass("hide");
                bonusButton.addClass("hide");
            };
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
                                    if (check_color["short"] != "yellow" && lineages[check_color["name"]].length == 1) {
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
                                    if (check_color["short"] != "yellow" && lineages[check_color["name"]].length == 1) {
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

    lineageOK() {
        // Check if the lineage is valid

        for (let color_index in annotationColors){
            let color = annotationColors[color_index];
            if (color["short"] in this.lineageCounts){
                let lineage = this.lineageCounts[color["short"]]
                // if (! ("total" in lineage && lineage["total"] && "name" in lineage && lineage["name"])){
                if ("total" in lineage && lineage["total"]  && ! ("name" in lineage && lineage["name"])){
                    console.log
                    return false;
                };
            };
        };

        return true;
    }

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


function downloadLineagesByColor(id) {
    treeLineagesCounts[id].showModalForm();
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