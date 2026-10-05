"use client";

/** Password stays in memory only and is cleared when the dialog closes. */
export function confirmAdminPassword(): Promise<string | null> {
  return new Promise((resolve) => {
    const dialog = document.createElement("dialog");
    dialog.className = "rounded-xl border border-white/20 bg-slate-900 p-6 text-white backdrop:bg-black/70";
    dialog.setAttribute("aria-labelledby", "admin-password-title");
    const form = document.createElement("form");
    const title = document.createElement("h2");
    title.id = "admin-password-title";
    title.textContent = "Confirm deletion";
    title.className = "mb-4 text-lg font-semibold";
    const label = document.createElement("label");
    label.textContent = "Your current password";
    const input = document.createElement("input");
    input.type = "password";
    input.autocomplete = "current-password";
    input.required = true;
    input.maxLength = 72;
    input.className = "mt-2 mb-4 block w-full rounded border border-white/20 bg-slate-800 p-2";
    label.append(input);
    const cancel = document.createElement("button");
    cancel.type = "button";
    cancel.textContent = "Cancel";
    cancel.className = "mr-4 rounded border border-white/20 px-4 py-2";
    const submit = document.createElement("button");
    submit.type = "submit";
    submit.textContent = "Confirm deletion";
    submit.className = "rounded bg-red-700 px-4 py-2";
    let result: string | null = null;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      result = input.value;
      dialog.close();
    });
    cancel.addEventListener("click", () => dialog.close());
    dialog.addEventListener("close", () => {
      input.value = "";
      dialog.remove();
      resolve(result);
      result = null;
    }, { once: true });
    form.append(title, label, cancel, submit);
    dialog.append(form);
    document.body.append(dialog);
    dialog.showModal();
    input.focus();
  });
}
