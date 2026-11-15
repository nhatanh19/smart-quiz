import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { AxiosError, InternalAxiosRequestConfig } from "axios";
import { AUTH_REQUEST_TIMEOUT_MS, apiClient } from "@/lib/apiClient";
import { AuthProvider } from "./AuthContext";
import ProtectedRoute from "@/routes/ProtectedRoute";
import { MemoryRouter } from "react-router-dom";

const originalAdapter = apiClient.defaults.adapter;

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter;
  cleanup();
});

it("passes AUTH_REQUEST_TIMEOUT_MS on /auth/me and exits loading state on timeout", async () => {
  let seenTimeout: number | undefined;
  apiClient.defaults.adapter = async (config: InternalAxiosRequestConfig) => {
    seenTimeout = config.timeout;
    throw new AxiosError("timeout of 15000ms exceeded", "ECONNABORTED", config);
  };

  render(
    <MemoryRouter>
      <AuthProvider>
        <ProtectedRoute>
          <p>Loaded</p>
        </ProtectedRoute>
      </AuthProvider>
    </MemoryRouter>,
  );

  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect(seenTimeout).toBe(AUTH_REQUEST_TIMEOUT_MS);
  expect(screen.getByRole("button", { name: "Thử lại" })).toBeTruthy();
});
