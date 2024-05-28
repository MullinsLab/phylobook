window.addEventListener("dragover",function(e){
    e = e || event;
    e.preventDefault();
},false);
window.addEventListener("drop",function(e){
    e = e || event;
    e.preventDefault();
},false);


function initializeDropzone() {
    Dropzone.options.myDropzone = {
        acceptedFiles: '.fasta,.zip',
        autoProcessQueue : false, // Prevents Dropzone from uploading dropped files immediately
        addRemoveLinks: true,
        uploadMultiple: true,
        parallelUploads: 100,
        maxFiles: 100,

        init: function() {
            var submitButton = document.querySelector("#submit-all")
            myDropzone = this;

            submitButton.addEventListener("click", function(e) {
            // Make sure that the form isn't actually being sent.
            e.preventDefault();
            e.stopPropagation();
            myDropzone.processQueue();
            });
        }
    };
};


function validProjectName() {
    projectName = $("#outer_project_name").val();

    if (! projectName) {
        alert("Please enter a project name.");
        return false;
    }

    return projectName;
}