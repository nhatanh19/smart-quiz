import React, { useRef, useState } from "react";
import {
  AlertCircle,
  Check,
  CheckCircle2,
  Copy,
  Download,
  File,
  FileText,
  LoaderCircle,
  RotateCcw,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import {
  DocumentParseResult,
  extractUploadErrorMessage,
  uploadAndExtractDocument,
} from "@/services/parserApi";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB (10,485,760 bytes)

type ParserStatus = "idle" | "selected" | "uploading" | "success" | "error";

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getFileExtension(filename: string): string {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex === -1) return "";
  return filename.slice(dotIndex).toLowerCase();
}

function validateFile(file: File): string | null {
  if (!file) {
    return "Vui lòng chọn một tệp tài liệu hợp lệ.";
  }
  if (file.size === 0) {
    return "Tệp tin rỗng (0 bytes). Vui lòng chọn tệp có nội dung.";
  }
  const ext = getFileExtension(file.name);
  if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
    return `Định dạng tệp "${file.name}" không được hỗ trợ. Hệ thống chỉ chấp nhận tệp .pdf, .docx, .txt.`;
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    return `Dung lượng tệp vượt quá 10MB (${sizeMB} MB). Vui lòng chọn tệp nhỏ hơn.`;
  }
  return null;
}

export const DocumentParserTab: React.FC = () => {
  const [status, setStatus] = useState<ParserStatus>("idle");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [parseResult, setParseResult] = useState<DocumentParseResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSelectFile = (file: File) => {
    const error = validateFile(file);
    if (error) {
      setErrorMessage(error);
      setSelectedFile(null);
      setParseResult(null);
      setStatus("error");
      return;
    }

    setSelectedFile(file);
    setErrorMessage(null);
    setParseResult(null);
    setStatus("selected");
  };

  const handleFileInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleSelectFile(file);
    }
    // Reset file input value to allow re-selecting same file
    if (event.target) {
      event.target.value = "";
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    if (status === "uploading") return;
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    if (status === "uploading") return;

    const file = event.dataTransfer.files?.[0];
    if (file) {
      handleSelectFile(file);
    }
  };

  const handleStartExtraction = async () => {
    if (!selectedFile) return;

    // Double-check validation before uploading
    const error = validateFile(selectedFile);
    if (error) {
      setErrorMessage(error);
      setStatus("error");
      return;
    }

    try {
      setStatus("uploading");
      setUploadProgress(0);
      setErrorMessage(null);

      const result = await uploadAndExtractDocument(
        selectedFile,
        (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(Math.min(percent, 99));
          }
        }
      );

      setUploadProgress(100);
      setParseResult(result);
      setStatus("success");
    } catch (err: unknown) {
      const msg = extractUploadErrorMessage(err);
      setErrorMessage(msg);
      setStatus("error");
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setParseResult(null);
    setErrorMessage(null);
    setUploadProgress(0);
    setStatus("idle");
    setCopied(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleCopyText = async () => {
    if (!parseResult?.raw_text) return;
    try {
      await navigator.clipboard.writeText(parseResult.raw_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback if clipboard API fails
      const textarea = document.createElement("textarea");
      textarea.value = parseResult.raw_text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const handleDownloadText = () => {
    if (!parseResult) return;
    const blob = new Blob([parseResult.raw_text], {
      type: "text/plain;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const baseName = parseResult.filename.replace(/\.[^/.]+$/, "");
    link.href = url;
    link.download = `${baseName}_extracted.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-6 text-white shadow-lg sm:p-8">
        <div className="max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-indigo-100">
            <Sparkles className="h-3.5 w-3.5 text-indigo-300" />
            MODULE 1: BÓC TÁCH TÀI LIỆU (FILE PARSER)
          </div>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Tải lên & Bóc tách văn bản thô
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Hỗ trợ trích xuất văn bản tự động từ các định dạng <strong>.PDF</strong>,{" "}
            <strong>.DOCX</strong>, <strong>.TXT</strong> với dung lượng tối đa 10MB.
            Bảo toàn chuẩn xác 100% tiếng Việt UTF-8 và bảng mã có dấu.
          </p>
        </div>
      </section>

      {/* Error Alert Banner */}
      {errorMessage && (
        <section
          role="alert"
          aria-live="assertive"
          className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-red-900 shadow-sm"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-red-950">Lỗi xử lý tệp tin</h3>
            <p className="mt-0.5 text-sm leading-6 text-red-800">{errorMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="rounded-lg p-1 text-red-600 hover:bg-red-100 transition"
            aria-label="Đóng thông báo lỗi"
          >
            <X className="h-4 w-4" />
          </button>
        </section>
      )}

      {/* Main Upload & Preview Area */}
      {status !== "success" ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileInputChange}
            accept=".pdf,.docx,.txt"
            className="hidden"
            id="document-upload-input"
          />

          {/* Drag & Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => {
              if (status !== "uploading") {
                fileInputRef.current?.click();
              }
            }}
            className={`group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 sm:p-12 text-center transition cursor-pointer ${
              isDragging
                ? "border-indigo-500 bg-indigo-50/70 ring-4 ring-indigo-100"
                : "border-slate-300 bg-slate-50/50 hover:border-indigo-400 hover:bg-slate-50"
            }`}
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 shadow-sm transition group-hover:scale-105 group-hover:bg-indigo-100">
              <UploadCloud className="h-8 w-8" />
            </div>

            <h3 className="mt-4 text-lg font-semibold text-slate-900">
              {isDragging ? "Thả tệp vào đây ngay!" : "Kéo & thả tệp tài liệu vào đây"}
            </h3>
            <p className="mt-1 text-sm text-slate-500">
              hoặc{" "}
              <span className="font-medium text-indigo-600 underline underline-offset-2">
                chọn tệp từ máy tính
              </span>
            </p>

            <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-xs text-slate-500">
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-200/70 px-2.5 py-1 font-mono font-medium text-slate-700">
                .PDF
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-200/70 px-2.5 py-1 font-mono font-medium text-slate-700">
                .DOCX
              </span>
              <span className="inline-flex items-center gap-1 rounded-md bg-slate-200/70 px-2.5 py-1 font-mono font-medium text-slate-700">
                .TXT
              </span>
              <span className="text-slate-400">• Dung lượng tối đa: 10MB</span>
            </div>
          </div>

          {/* Selected File Card */}
          {selectedFile && (
            <div className="mt-6 rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 sm:p-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-sm">
                    <FileText className="h-6 w-6" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-slate-900" title={selectedFile.name}>
                      {selectedFile.name}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {formatFileSize(selectedFile.size)} • Định dạng:{" "}
                      <span className="font-mono uppercase font-semibold text-indigo-700">
                        {getFileExtension(selectedFile.name).replace(".", "")}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={handleReset}
                    disabled={status === "uploading"}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                  >
                    <X className="h-4 w-4" />
                    Đổi tệp
                  </button>

                  <button
                    type="button"
                    onClick={handleStartExtraction}
                    disabled={status === "uploading"}
                    className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {status === "uploading" ? (
                      <>
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                        <span>Đang xử lý... ({uploadProgress}%)</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        <span>Bắt đầu bóc tách</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Progress Bar while uploading */}
              {status === "uploading" && (
                <div className="mt-4 space-y-1.5">
                  <div className="flex justify-between text-xs font-medium text-indigo-900">
                    <span>
                      {uploadProgress < 100
                        ? "Đang tải tệp lên máy chủ..."
                        : "Đang bóc tách và trích xuất văn bản thô..."}
                    </span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-indigo-200">
                    <div
                      className="h-full bg-indigo-600 transition-all duration-300 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* Extracted Raw Text Viewer (Success State) */
        parseResult && (
          <div className="space-y-4">
            {/* Success Summary Header */}
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-6 shadow-sm">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-600 text-white shadow-sm">
                    <CheckCircle2 className="h-6 w-6" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-lg font-semibold text-emerald-950">
                        Bóc tách thành công
                      </h2>
                      <span className="rounded-full bg-emerald-200/80 px-2.5 py-0.5 text-xs font-mono font-semibold text-emerald-900 uppercase">
                        .{parseResult.file_type || "txt"}
                      </span>
                    </div>
                    <p className="mt-0.5 text-xs text-emerald-800 break-all font-mono">
                      {parseResult.filename}
                    </p>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={handleCopyText}
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-4 py-2 text-sm font-semibold transition shadow-sm ${
                      copied
                        ? "border-emerald-600 bg-emerald-600 text-white"
                        : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    {copied ? (
                      <>
                        <Check className="h-4 w-4" />
                        Đã sao chép!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4" />
                        Sao chép nội dung
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    onClick={handleDownloadText}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 shadow-sm"
                  >
                    <Download className="h-4 w-4" />
                    Tải về (.txt)
                  </button>

                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 shadow-sm"
                  >
                    <RotateCcw className="h-4 w-4" />
                    Bóc tách tệp khác
                  </button>
                </div>
              </div>

              {/* Statistics Metadata Badges */}
              <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4 pt-4 border-t border-emerald-200/70 text-xs">
                <div className="rounded-lg bg-white/80 p-2.5 border border-emerald-100">
                  <span className="text-slate-500">Dung lượng tệp</span>
                  <p className="mt-1 font-semibold text-slate-900 font-mono">
                    {formatFileSize(parseResult.file_size)}
                  </p>
                </div>
                <div className="rounded-lg bg-white/80 p-2.5 border border-emerald-100">
                  <span className="text-slate-500">Tổng số từ</span>
                  <p className="mt-1 font-semibold text-slate-900 font-mono">
                    {parseResult.word_count.toLocaleString("vi-VN")} từ
                  </p>
                </div>
                <div className="rounded-lg bg-white/80 p-2.5 border border-emerald-100">
                  <span className="text-slate-500">Tổng số ký tự</span>
                  <p className="mt-1 font-semibold text-slate-900 font-mono">
                    {parseResult.character_count.toLocaleString("vi-VN")} ký tự
                  </p>
                </div>
                <div className="rounded-lg bg-white/80 p-2.5 border border-emerald-100">
                  <span className="text-slate-500">
                    {parseResult.page_count ? "Số trang tài liệu" : "Bảng mã văn bản"}
                  </span>
                  <p className="mt-1 font-semibold text-slate-900 font-mono">
                    {parseResult.page_count
                      ? `${parseResult.page_count} trang`
                      : "UTF-8 Tiếng Việt"}
                  </p>
                </div>
              </div>
            </div>

            {/* Scrollable Preformatted Raw Text Box */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 sm:p-6 shadow-xl">
              <div className="mb-3 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center gap-2">
                  <File className="h-4 w-4 text-indigo-400" />
                  <span className="font-semibold text-slate-200 uppercase tracking-wider">
                    Văn bản thô đã bóc tách (Raw Extracted Content)
                  </span>
                </div>
                <span className="font-mono text-slate-500">UTF-8 Encoded</span>
              </div>

              <div
                tabIndex={0}
                role="region"
                aria-label="Văn bản thô đã trích xuất"
                className="max-h-[550px] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900/90 p-4 sm:p-5 font-mono text-sm leading-relaxed text-slate-100 selection:bg-indigo-600 selection:text-white whitespace-pre-wrap break-words"
              >
                {parseResult.raw_text.trim().length > 0 ? (
                  parseResult.raw_text
                ) : (
                  <span className="italic text-slate-500">
                    (Tài liệu không chứa nội dung văn bản có thể trích xuất)
                  </span>
                )}
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
};

export default DocumentParserTab;
