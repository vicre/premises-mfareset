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
    let activePopover = null;

    const triggers = document.querySelectorAll('[data-bs-toggle="popover"]');

    triggers.forEach(el => {
        const popover = new bootstrap.Popover(el, {
            trigger: 'manual',   // we control it ourselves
            container: 'body'
        });

        el.addEventListener('click', function (e) {
            e.stopPropagation();

            // Close currently open popover if it's not this one
            if (activePopover && activePopover !== popover) {
                activePopover.hide();
            }

            // Toggle current
            if (activePopover === popover) {
                popover.hide();
                activePopover = null;
            } else {
                popover.show();
                activePopover = popover;
            }
        });
    });

    // Click outside → close
    document.addEventListener('click', function (e) {
        if (!activePopover) return;

        const popoverEl = document.querySelector('.popover');

        if (
            popoverEl &&
            !popoverEl.contains(e.target) &&
            !e.target.closest('[data-bs-toggle="popover"]')
        ) {
            activePopover.hide();
            activePopover = null;
        }
    });
});
// #### This logic is for the question-label's #### ends here ####