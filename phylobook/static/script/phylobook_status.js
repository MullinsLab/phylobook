class processStatus {
    processes = [];
    lastCount = undefined;
    running = 0;
    pending = 0;
    failed = 0;
    modal = undefined;
    modalBody = undefined;

    constructor() {
        this.modal = $("#processModal");
        this.modalBody = $("#processModalBody");

        console.log("processStatus object created");
    }

    update() {
        let self = window.processStatus;
        $.ajax({
            url: "/projects/import_project/status",
            type: "GET",
            success: function(data) {
                self.processes = data.processes;
                self.running = data.running;
                self.pending = data.pending;
                self.failed = data.failed;

                self.setNotification();
                self.modalBody.html(self.modalHTML());
            },
        });
    }

    setNotification() {
        if (this.lastCount === undefined || this.lastCount != this.processes.length) {
            $("#processNotification").html(this.buttonHTML());
            $("#processButton").on("click", function() {window.processStatus.modalShow();});
            $("#processModalRefreshButton").on("click", function() {window.processStatus.update();});
            
            this.lastCount = this.processes.length;
        };
    }

    buttonHTML() {
        let html = `&nbsp;&nbsp;
            <button type="button" class="btn btn-outline-${this.buttonType()} btn-sm" id="processButton">
            ${this.buttonText()}
            ${this.buttonCount()}
            ${this.buttonFailed()}
            </button>&nbsp;&nbsp;`
        return html;
    }

    buttonText() {
        return "Imports"
    }

    buttonCount() {
        return `<span class="badge badge-light">${this.running}/${this.processes.length}</span>`;
    }

    buttonFailed() {
        if (this.failed == 0) {
            return "";
        }

        return `<span class="badge badge-danger">${this.failed} failed!</span>`;
    }

    buttonType() {
        if (this.processes.length == 0) {
            return "secondary";
        }
        else if (this.failed > 0) {
            return "danger";
        }
        return "success";    
    }

    modalShow() {
        this.modal.modal("show");
    }

    modalHTML() {
        let html = this.modalDefaultText();
        let lastProject = "";

        for (let processIndex = 0; processIndex < this.processes.length; processIndex++) {
            if (this.processes[processIndex].project != lastProject) {
                html += this.modalProjectHTML(this.processes[processIndex]);
                lastProject = this.processes[processIndex].project;
            }

            html += this.modalProcessHTML(this.processes[processIndex]);
        }

        html += "</ul>";

        return html;
    }

    modalDefaultText() {
        if (this.processes.length == 0) {
            return "No import processes running";
        }

        return `<p>There are ${this.running} import processes running, ${this.pending} pending, and ${this.failed} failed.</p>`;
    }

    modalProjectHTML(project) {
        return `<h5>Project: ${project.project}</h5><ul>`
    }

    modalProcessHTML(process) {
        let html = "<li>";

        html += `${process.tree} ${this.modalStatusHTML(process.status)}`;

        return html
    }

    modalStatusHTML(status) {
        if (status == "Running") {
            return `<span class="badge badge-success">${status}</span>`;
        }
        else if (status == "Pending") {
            return `<span class="badge badge-secondary">${status}</span>`;
        }
        else if (status == "Failed") {
            return `<span class="badge badge-danger">${status}</span>`;
        }
    }
}