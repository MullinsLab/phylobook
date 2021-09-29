function showhideColorRange(id, tag) {
    var text = tag.innerHTML;
    if (text.startsWith("Show")) {
        tag.innerHTML = "Hide color range";
        $("#" + id).removeClass("hide");
    } else {
        tag.innerHTML = "Show color range";
        $("#" + id).addClass("hide");
    }
}

function resizeHighlighterWidth(imgparentid, adjustment) {
    var imgheight = $('#' + imgparentid).find('img').prop("naturalHeight");
    var imgwidth = $('#' + imgparentid).find('img').prop("naturalWidth");
    var imgratio = imgwidth/imgheight;
    var imgimagewidth = adjustment * imgratio;
    $('#' + imgparentid).find('.highlighter').width(imgimagewidth);
}

function resizeSVGWidth(imgparentid, adjustment) {
    var svgheight = $('#' + imgparentid).find('svg').attr('height');
    var svgwidth = $('#' + imgparentid).find('svg').attr('width');
    var svgratio = svgwidth/svgheight;
    var svgimagewidth = adjustment * svgratio;
    $('#' + imgparentid).find('.svgimage').width(svgimagewidth);
}

$(document).ready(function() {
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