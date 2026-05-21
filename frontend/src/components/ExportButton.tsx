import { Download } from "lucide-react";
import { useState } from "react";

import { exportResumePDF } from "../api/export";
import type { ResumeContactInfo, ResumeJSON } from "../types";

interface ExportButtonProps {
  resume: ResumeJSON;
  contactInfo?: ResumeContactInfo;
  className?: string;
  disabled?: boolean;
}

function filenameFromResume(resume: ResumeJSON): string {
  const name = resume.candidate_name.trim() || "resume";
  return `${name.replace(/\s+/g, "_")}_resume.pdf`;
}

export default function ExportButton({
  resume,
  contactInfo,
  className = "",
  disabled = false,
}: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState("");

  async function handleExport() {
    setIsExporting(true);
    setError("");
    try {
      const blob = await exportResumePDF(resume, contactInfo);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filenameFromResume(resume);
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "PDF 导出失败");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className={className}>
      <button
        type="button"
        onClick={handleExport}
        disabled={disabled || isExporting}
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-md bg-action px-4 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300"
      >
        <Download className="h-4 w-4" aria-hidden="true" />
        {isExporting ? "导出中..." : "导出 PDF"}
      </button>
      {error && (
        <p className="mt-2 rounded-lg border border-rose-100 bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}
