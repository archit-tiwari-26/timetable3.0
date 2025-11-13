import React from "react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";

export default function DownloadPDF({ targetId, filename }) {
  async function handleDownload() {
    const original = document.getElementById(targetId);
    if (!original) return alert("Element not found");

    // ---- 1) Clone the timetable OUTSIDE scroll container ----
    const clone = original.cloneNode(true);
    clone.style.position = "absolute";
    clone.style.left = "-9999px";       // hide off-screen
    clone.style.top = "0";
    clone.style.maxWidth = "none";      // remove Tailwind restrictions
    clone.style.width = "fit-content";  // allow full expansion
    clone.style.overflow = "visible";

    document.body.appendChild(clone);

    // Get true width & height from the clone
    const realWidth = clone.scrollWidth;
    const realHeight = clone.scrollHeight;

    // ---- 2) Render the CLONE, not the original ----
    const canvas = await html2canvas(clone, {
      scale: 2,
      useCORS: true,
      windowWidth: realWidth,
      windowHeight: realHeight,
      backgroundColor: "#ffffff",
    });

    document.body.removeChild(clone); // cleanup clone

    const imgData = canvas.toDataURL("image/png");
    const imgWidth = canvas.width;
    const imgHeight = canvas.height;

    // ---- 3) Create a PDF with EXACT same size ----
    const pdf = new jsPDF({
      orientation: imgWidth > imgHeight ? "l" : "p",
      unit: "px",
      format: [imgWidth, imgHeight],
    });

    pdf.addImage(imgData, "PNG", 0, 0, imgWidth, imgHeight);
    pdf.save(filename);
  }

  return (
    <button
      onClick={handleDownload}
      className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
    >
      ⬇️ Download PDF
    </button>
  );
}
