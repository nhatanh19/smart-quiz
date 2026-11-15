import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  withCredentials: true,
});

let refreshing: Promise<unknown> | null = null;
let endingSession = false;
let logoutRequest: Promise<void> | null = null;

// Finish any refresh before deleting cookies so its response cannot restore them.
export function logoutSession(): Promise<void> {
  if (logoutRequest) return logoutRequest;
  endingSession = true;
  logoutRequest = (async () => {
    try {
      await refreshing?.catch(() => undefined);
      await apiClient.post("/auth/logout");
    } finally {
      endingSession = false;
      logoutRequest = null;
    }
  })();
  return logoutRequest;
}

apiClient.interceptors.response.use(response => response, async error => {
  const config = error.config;
  if (!endingSession && error.response?.status === 401 && config && !config._retried &&
      !/\/auth\/(login|register|refresh|logout)/.test(config.url || "")) {
    config._retried = true;
    refreshing ||= apiClient.post("/auth/refresh").finally(() => { refreshing = null; });
    await refreshing;
    return apiClient(config);
  }
  return Promise.reject(error);
});

export function authError(error: unknown): string {
  if (!axios.isAxiosError(error)) return "Đã xảy ra lỗi. Vui lòng thử lại.";
  const detail = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return [...new Set(detail.map(item => {
    const field = item.loc?.[item.loc.length - 1];
    if (field === "email") return "Email không hợp lệ.";
    if (field === "password") return "Mật khẩu cần ít nhất 8 ký tự và tối đa 72 byte UTF-8.";
    if (field === "full_name") return "Vui lòng nhập họ tên hợp lệ.";
    if (field === "role") return "Vui lòng chọn tài khoản học sinh hoặc giáo viên.";
    return "Thông tin không hợp lệ.";
  }))].join(" ");
  return error.response ? "Không thể xử lý yêu cầu. Vui lòng thử lại." : "Không thể kết nối máy chủ. Vui lòng kiểm tra kết nối.";
}

/**
 * Extract a user-facing message from Axios / FastAPI error responses (including 422 arrays).
 */
export function extractApiError(
  error: unknown,
  fallback = "Đã xảy ra lỗi không xác định.",
): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          typeof item === "object" && item && "msg" in item
            ? String((item as { msg: unknown }).msg)
            : typeof item === "string"
              ? item
              : "",
        )
        .filter(Boolean);
      if (messages.length > 0) return messages.join(", ");
    } else if (detail && typeof detail === "object" && "msg" in detail) {
      return String((detail as { msg: unknown }).msg);
    }
    if (!error.response) {
      return "Không thể kết nối tới máy chủ. Vui lòng thử lại.";
    }
    return error.message || "Không thể xử lý yêu cầu. Vui lòng thử lại.";
  }
  if (error instanceof Error && error.message.trim()) return error.message;
  return fallback;
}
