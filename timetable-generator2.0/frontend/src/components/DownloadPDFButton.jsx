import React from "react";
import API from "../api";

export default function DownloadPDFButton({
  label = "Download PDF",
  filename = "full_timetable.pdf",
  endpoint = "/timetable/full/pdf/"
}) {
  async function handleDownload() {
    try {
      const response = await API.get(endpoint, {
        responseType: "blob",
      });

      const blob = new Blob([response.data], {
        type: "application/pdf",
      });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();

      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF Download Error:", err);
      alert("Failed to download PDF");
    }
  }

  return (
    <button
      onClick={handleDownload}
      className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg shadow"
    >
      {label}
    </button>
  );
}
