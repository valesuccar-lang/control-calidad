/**
 * Report generation utilities — PDF via jsPDF, Excel via xlsx
 */
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";

export interface InspectionRow {
  inspection_id: string;
  lote_id: string;
  defect_id: string;
  comment_text: string;
  machine_id: string;
  analista_id: string;
  check_in: string;
  sync_status: string;
}

export function exportToPDF(rows: InspectionRow[], title = "Inspecciones") {
  const doc = new jsPDF();
  doc.setFontSize(16);
  doc.text(title, 14, 15);
  doc.setFontSize(10);
  doc.text(`Generado: ${new Date().toLocaleString("es-CO")}`, 14, 22);

  autoTable(doc, {
    startY: 28,
    head: [["ID", "Lote", "Defecto", "Máquina", "Estado", "Fecha"]],
    body: rows.map((r) => [
      r.inspection_id.slice(0, 8),
      r.lote_id,
      r.defect_id,
      r.machine_id,
      r.sync_status,
      new Date(r.check_in).toLocaleDateString("es-CO"),
    ]),
    styles: { fontSize: 8 },
  });

  doc.save(`${title.toLowerCase().replace(/\s+/g, "-")}-${Date.now()}.pdf`);
}

export function exportToExcel(rows: InspectionRow[], filename = "inspecciones") {
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Inspecciones");
  XLSX.writeFile(wb, `${filename}-${Date.now()}.xlsx`);
}
