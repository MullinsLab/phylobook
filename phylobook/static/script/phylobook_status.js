class processStatus {
    processes = [];
    lastCount = undefined;

    constructor() {
        console.log("processStatus object created");
    }

    update() {
        let self = this;
        $.ajax({
            url: "/projects/import_project/status",
            type: "GET",
            success: function(data) {
                self.processes = data.processes;
                console.log(self.processes);
                self.setNotification();
            },
        });
    }

    setNotification() {
        if (this.lastCount === undefined || this.lastCount != this.processes.length) {
            $("#processNotification").html(this.buttonHTML());
            console.log(this.buttonHTML());
        };
    }

    buttonHTML() {
        return `&nbsp;&nbsp;<button type="button" class="btn btn-outline-${this.buttonType()} btn-sm">${this.buttonText()} <span class="badge badge-light">${this.buttonCount()}</span></button>&nbsp;&nbsp;`
    }

    buttonText() {
        if (this.processes.length == 0) {
            return "No processes running";
        }
        else {
            return "Processes running";
        }
    }

    buttonCount() {
        console.log(this.processes.length)
        return this.processes.length;
    }

    buttonType() {
        return "secondary"
    }
}