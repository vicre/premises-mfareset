// #### This is for the AJAX #### starts here #### //
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("reset-mfa-form");
    const statusBox = document.getElementById("reset-status");

    if (!form || !statusBox) return;

    const submitButton = form.querySelector('button[type="submit"]');
    const passkeyCheckbox = document.getElementById("include_fido2");
    const confirmation = document.getElementById("reset-confirmation");
    const confirmButton = document.getElementById("confirm-reset");
    const cancelButton = document.getElementById("cancel-reset");
    let submitting = false;
    let pendingFormData = null;

    function showStatus(kind, message) {
        const alert = document.createElement("div");
        alert.className = `alert alert-${kind}`;
        alert.textContent = message;
        statusBox.replaceChildren(alert);
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();
        if (submitting) return;

        const target = form.elements.namedItem("target_upn").value;
        const scope = passkeyCheckbox.checked
            ? `Alle brugerens passkeys / FIDO2-sikkerhedsnøgler slettes også (${form.dataset.passkeyCount} fundet ved opslag).`
            : "Passkeys / FIDO2-sikkerhedsnøgler bevares.";
        document.getElementById("reset-confirmation-target").textContent = target;
        document.getElementById("reset-confirmation-scope").textContent = scope;
        pendingFormData = new FormData(form);
        confirmation.showModal();
    });

    cancelButton.addEventListener("click", () => confirmation.close());
    confirmation.addEventListener("close", () => { pendingFormData = null; });

    confirmButton.addEventListener("click", async function () {
        if (submitting || !pendingFormData) return;
        // Use the scope shown in the dialog, captured before controls are disabled.
        const formData = pendingFormData;
        pendingFormData = null;
        confirmation.close();
        submitting = true;
        submitButton.disabled = true;
        passkeyCheckbox.disabled = true;
        showStatus("info", "Resetting MFA...");
        let succeeded = false;

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
                succeeded = true;
                window.location.reload();
            } else {
                showStatus("danger", data.message || "Reset failed.");
            }
        } catch (error) {
            showStatus("danger", `Unexpected error: ${error}`);
        } finally {
            if (!succeeded) {
                submitting = false;
                submitButton.disabled = false;
                passkeyCheckbox.disabled = false;
            }
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
