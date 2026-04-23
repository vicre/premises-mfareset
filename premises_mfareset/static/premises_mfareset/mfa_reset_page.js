// #### This is for the AJAX #### starts here #### //
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("reset-mfa-form");
    const statusBox = document.getElementById("reset-status");

    if (!form || !statusBox) return;

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        statusBox.innerHTML = '<div class="alert alert-info">Resetting MFA...</div>';

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            const data = await response.json();

            if (response.ok && data.success) {
                statusBox.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
            } else {
                statusBox.innerHTML = `<div class="alert alert-danger">${data.message || "Reset failed."}</div>`;
            }
        } catch (error) {
            statusBox.innerHTML = `<div class="alert alert-danger">Unexpected error: ${error}</div>`;
        }
    });
});
// #### This is for the AJAX #### ends here #### //


// #### This logic is for the question-label's #### starts here ####
document.addEventListener("DOMContentLoaded", function () {
    let activeTrigger = null;
    const triggers = document.querySelectorAll('[data-bs-toggle="popover"]');

    triggers.forEach(trigger => {
        const popover = new bootstrap.Popover(trigger, {
            trigger: "manual",
            container: "body",
            html: false
        });

        function showPopover() {
            if (activeTrigger && activeTrigger !== trigger) {
                bootstrap.Popover.getInstance(activeTrigger)?.hide();
            }
            popover.show();
            activeTrigger = trigger;
        }

        function hidePopover() {
            popover.hide();
            if (activeTrigger === trigger) {
                activeTrigger = null;
            }
        }

        trigger.addEventListener("mouseenter", showPopover);
        trigger.addEventListener("focus", showPopover);

        trigger.addEventListener("mouseleave", function () {
            setTimeout(() => {
                const popoverEl = document.querySelector(".popover:hover");
                if (!popoverEl) {
                    hidePopover();
                }
            }, 100);
        });

        trigger.addEventListener("blur", hidePopover);

        trigger.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();

            if (activeTrigger === trigger) {
                hidePopover();
            } else {
                showPopover();
            }
        });
    });

    document.addEventListener("click", function (e) {
        if (!activeTrigger) return;

        const popoverEl = document.querySelector(".popover");
        if (
            popoverEl &&
            !popoverEl.contains(e.target) &&
            !e.target.closest('[data-bs-toggle="popover"]')
        ) {
            bootstrap.Popover.getInstance(activeTrigger)?.hide();
            activeTrigger = null;
        }
    });
});
// #### This logic is for the question-label's #### ends here ####