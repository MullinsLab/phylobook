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
        // acceptedFiles: '.fasta,.zip',
        autoProcessQueue : false, // Prevents Dropzone from uploading dropped files immediately
        addRemoveLinks: true,
        uploadMultiple: true,
        parallelUploads: 100,
        maxFiles: 100,

        init: function() {
            var submitButton = document.querySelector("#submit-all")
            myDropzone = this;

            submitButton.addEventListener("click", function(e) {
                e.preventDefault();
                e.stopPropagation();

                var active = $("ul#type_tab a.active").attr("id");
                console.log(active);

                if (! validProjectName()) {
                    return;
                };

                console.log($("#project_name").val());
                console.log(`Project name: ${projectName}`);

                $("#project_name").val(projectName);
                $("#project_type").val(active.split("_")[0]);
                console.log($("#project_name").val());

                myDropzone.processQueue();
            });

            this.on("successmultiple", function(files, response) {
                if (response.error){
                    alert(response.error);
                }
                else if (response.success) {
                    alert(response.success);
                }
            });
        }
    };
};


function validProjectName() {
    projectName = $("#new_outer_project_name").val();
    console.log(projectName);

    if (! projectName) {
        alert("Please enter a project name.");
        return false;
    }

    if (hasWhiteSpace(projectName)) {
        alert("Project name cannot contain spaces.");
        return false;
    }

    var available = false;
    $.ajax({
        url: `/projects/project_name_available/${projectName}`,
        type: 'GET',
        async: false,
        success: function(response) {
            if (! response.available) {
                alert(`A project with this name already exists:\n "${projectName}"\n\nPlease enter a different name.`);
                available = false;
            }
        }
    });

    return true;
}


function hasWhiteSpace(string) {
    return /\s/g.test(string);
}