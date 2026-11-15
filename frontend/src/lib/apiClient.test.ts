import { afterEach, expect, it, vi } from "vitest";
import { AxiosError, AxiosResponse, InternalAxiosRequestConfig } from "axios";
import { apiClient, logoutSession } from "./apiClient";

const originalAdapter = apiClient.defaults.adapter;
afterEach(() => { apiClient.defaults.adapter = originalAdapter; });

it.each([false, true])("finishes refresh before logout, including refresh failure=%s", async failRefresh => {
  const calls: string[] = [];
  let release!: () => void;
  const gate = new Promise<void>(resolve => { release = resolve; });
  function response(config: InternalAxiosRequestConfig, status = 200): AxiosResponse {
    return { data: {}, status, statusText: "", headers: {}, config };
  }
  function unauthorized(config: InternalAxiosRequestConfig) {
    return new AxiosError("Unauthorized", "ERR_BAD_REQUEST", config, undefined, response(config, 401));
  }
  apiClient.defaults.adapter = async config => {
    if (config.url === "/auth/refresh") {
      calls.push("refresh");
      await gate;
      if (failRefresh) throw unauthorized(config);
    } else if (config.url === "/auth/logout") {
      calls.push("logout");
    } else if (!(config as InternalAxiosRequestConfig & { _retried?: boolean })._retried) {
      throw unauthorized(config);
    }
    return response(config);
  };
  const checking = apiClient.get("/auth/me").catch(() => undefined);
  await vi.waitFor(() => expect(calls).toEqual(["refresh"]));
  const ending = logoutSession();
  expect(logoutSession()).toBe(ending);
  await expect(apiClient.get("/protected")).rejects.toThrow("Unauthorized");
  expect(calls).toEqual(["refresh"]);
  release();
  await Promise.all([checking, ending]);
  expect(calls).toEqual(["refresh", "logout"]);
});
