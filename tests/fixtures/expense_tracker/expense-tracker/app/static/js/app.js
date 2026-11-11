// Calls only the paths declared in the Contract.
const API = {
  categories: "/api/categories",
  expenses: "/api/expenses",
  summary: "/api/summary",
};

const $ = (sel) => document.querySelector(sel);
let categories = [];

async function request(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    } catch (_) { /* no JSON body */ }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

function showError(message) {
  const el = $("#error");
  el.textContent = message || "";
  el.hidden = !message;
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

async function loadCategories() {
  categories = await request("GET", API.categories);
  $("#category-list").innerHTML = categories
    .map((c) => `<li>${escapeHtml(c.name)} <button data-delete-category="${c.id}">Delete</button></li>`)
    .join("");
  $("#expense-form select[name=category_id]").innerHTML = categories
    .map((c) => `<option value="${c.id}">${escapeHtml(c.name)}</option>`)
    .join("");
}

async function loadExpenses() {
  const expenses = await request("GET", API.expenses);
  const names = Object.fromEntries(categories.map((c) => [c.id, c.name]));
  $("#expense-list").innerHTML = expenses
    .map(
      (e) => `<tr>
        <td>${escapeHtml(e.date)}</td>
        <td>${escapeHtml(e.description)}</td>
        <td>${escapeHtml(names[e.category_id] || "?")}</td>
        <td>${e.amount.toFixed(2)}</td>
        <td>${escapeHtml(e.note)}</td>
        <td>
          <button data-edit-expense="${e.id}">Edit</button>
          <button data-delete-expense="${e.id}">Delete</button>
        </td>
      </tr>`
    )
    .join("");
}

function resetExpenseForm() {
  const form = $("#expense-form");
  form.reset();
  form.elements.expense_id.value = "";
  $("#expense-form-title").textContent = "Add expense";
  $("#cancel-edit").hidden = true;
}

async function startEdit(id) {
  const e = await request("GET", `${API.expenses}/${id}`);
  const form = $("#expense-form");
  form.elements.expense_id.value = e.id;
  form.elements.amount.value = e.amount;
  form.elements.description.value = e.description;
  form.elements.date.value = e.date;
  form.elements.category_id.value = e.category_id;
  form.elements.note.value = e.note ?? "";
  $("#expense-form-title").textContent = "Edit expense";
  $("#cancel-edit").hidden = false;
}

async function run(action) {
  try {
    showError("");
    await action();
  } catch (err) {
    showError(err.message);
  }
}

$("#category-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  run(async () => {
    await request("POST", API.categories, { name: ev.target.elements.name.value.trim() });
    ev.target.reset();
    await loadCategories();
  });
});

$("#expense-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const form = ev.target;
  const body = {
    amount: parseFloat(form.elements.amount.value),
    description: form.elements.description.value,
    date: form.elements.date.value,
    category_id: parseInt(form.elements.category_id.value, 10),
    note: form.elements.note.value || null,
  };
  run(async () => {
    if (form.elements.expense_id.value) {
      await request("PUT", `${API.expenses}/${form.elements.expense_id.value}`, body);
    } else {
      await request("POST", API.expenses, body);
    }
    resetExpenseForm();
    await loadExpenses();
  });
});

$("#cancel-edit").addEventListener("click", resetExpenseForm);

$("#summary-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  run(async () => {
    const month = ev.target.elements.month.value;
    const s = await request("GET", `${API.summary}?month=${encodeURIComponent(month)}`);
    $("#summary-result").textContent = `${s.month}: ${s.count} expense(s), total ${s.total.toFixed(2)}`;
  });
});

document.addEventListener("click", (ev) => {
  const t = ev.target;
  if (t.dataset.deleteCategory) {
    run(async () => {
      await request("DELETE", `${API.categories}/${t.dataset.deleteCategory}`);
      await loadCategories();
    });
  } else if (t.dataset.deleteExpense) {
    run(async () => {
      await request("DELETE", `${API.expenses}/${t.dataset.deleteExpense}`);
      await loadExpenses();
    });
  } else if (t.dataset.editExpense) {
    run(() => startEdit(t.dataset.editExpense));
  }
});

run(async () => {
  await loadCategories();
  await loadExpenses();
});
