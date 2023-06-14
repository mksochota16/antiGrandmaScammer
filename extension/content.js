function main(request, sender, sendResponse) {
  if (request.action === "checkUrl") {
    const apiUrl = `https://localhost/check?url=${encodeURIComponent(
      window.location.href
    )}`;

    fetch(apiUrl)
      .then((response) => response.json())
      .then((data) => {
        if (data.isMalicious) {
          prependWarningBanner();
        }
      })
      .catch((error) => console.error(error));
  }
}

function prependWarningBanner() {
  const banner = document.createElement("div");
  banner.style.position = "fixed";
  banner.style.bottom = "0";
  banner.style.left = "0";
  banner.style.width = "100%";
  banner.style.height = "150px";
  banner.style.backgroundColor = "red";
  banner.style.color = "white";
  banner.style.padding = "20px";
  banner.style.textAlign = "center";
  banner.style.fontSize = "75px";
  banner.style.zIndex = "9999";
  banner.textContent = "Scam warning";

  document.body.prepend(banner);
}
 
main();
