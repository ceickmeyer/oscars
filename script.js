const exportButton = document.getElementById("export-button");

exportButton.addEventListener("click", () => {
  html2canvas(document.body, { width: 700 }).then((canvas) => {
    const imgData = canvas.toDataURL("image/jpeg");
    const link = document.createElement("a");
    link.href = imgData;
    link.download = "awards-selections.jpg";
    link.click();
  });
});
