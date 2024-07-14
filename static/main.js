let query = document.getElementById("query");
let results_div = document.getElementById("results");

const entries = document.querySelectorAll("p#entry");
entries.forEach(entry => {
  entry.addEventListener("click", function(event) {
    event.preventDefault();
    // alert('Entry link clicked: ' + this.textContent);
    showSummary(this.textContent);
  })
})

function showSummary(title) {
  fetch("/summary", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ article_title: title }),
  })
    .then((result) => result.json())
    .then((result) => alert(result));
}

function show(results) {
  results_div.textContent = "";
  results.forEach((entry) => {
    let link = document.createElement("a");
    let title = document.createElement("p");
    let datetime = document.createElement("p");

    link.target = "_blank";

    title.innerHTML = entry.title;
    title.classList.add("title");

    title.addEventListener('click', function(event) {
      event.preventDefault();
      // alert('Entry link clicked: ' + this.textContent);
      showSummary(this.textContent);
    });

    datetime.innerHTML = entry.datetime;
    datetime.classList.add("datetime");

    link.appendChild(title);
    link.appendChild(datetime);
    link.href = entry.url;


    results_div.appendChild(link);
  });
}

query.addEventListener("input", () => {
  if (query.value != "") {
    fetch("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query.value }),
    })
      .then((results) => results.json())
      .then((results) => show(results));
  } else {
    show(all_results);
  }
});


