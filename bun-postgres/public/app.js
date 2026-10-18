document.addEventListener("click", function (event) {
  if (event.target.closest("#add-column")) {
    const index = document.querySelectorAll(".column-edit").length;
    if (index >= 50) return;
    htmx.ajax("GET", "/columns?index=" + index, {
      target: "#columns",
      swap: "beforeend",
    });
  }
});
document.addEventListener("change", function (event) {
  if (event.target.matches('select[name^="mode_"]')) {
    const input = event.target.parentElement.querySelector("input");
    input.disabled = event.target.value !== "value";
    if (!input.disabled) input.focus();
  }
});
document.addEventListener("keydown", function (event) {
  if (
    event.target.matches(".sql-editor") &&
    event.key === "Enter" &&
    (event.ctrlKey || event.metaKey)
  ) {
    event.preventDefault();
    event.target.form.requestSubmit();
  }
});
for (const name of ["htmx:responseError", "htmx:sendError"])
  document.addEventListener(name, function () {
    const box = document.querySelector("#network-error");
    if (box) {
      box.hidden = false;
      box.textContent =
        "Request failed. Check your connection and refresh before retrying a write.";
    }
  });
