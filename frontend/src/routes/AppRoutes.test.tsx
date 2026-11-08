import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import AppRoutes from "./AppRoutes";
import { User, UserRole } from "@/types";

const auth = vi.hoisted(() => ({
  user: null as User | null, loading: false, error: "",
  ensureSession: vi.fn().mockResolvedValue(undefined),
  logout: vi.fn().mockResolvedValue(undefined), login: vi.fn(),
}));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => auth }));

function Location() {
  return <span data-testid="location">{useLocation().pathname}</span>;
}
function open(path: string) {
  render(<MemoryRouter initialEntries={[path]}><AppRoutes /><Location /></MemoryRouter>);
}
function user(role: UserRole): User {
  return { id: "user-id", email: "an@example.com", full_name: "Nguyễn Văn An", role,
    is_active: true, created_at: "", updated_at: "" };
}
beforeEach(() => {
  auth.user = user("STUDENT");
  auth.loading = false;
  auth.error = "";
  auth.logout.mockResolvedValue(undefined);
});
afterEach(cleanup);

describe("role protected routes", () => {
  it.each(["/instructor/parser", "/instructor/ai-generator", "/instructor/exams/new", "/parser", "/ai-generator", "/analytics", "/admin/users"])("blocks student at %s", path => {
    open(path);
    expect(screen.getByRole("heading", { name: /403/ })).toBeTruthy();
    expect(screen.queryByText("Parser (M1)")).toBeNull();
  });
  it.each(["INSTRUCTOR", "ADMIN"] as UserRole[])("allows %s to manage question bank", role => {
    auth.user = user(role);
    open("/instructor/ai-generator");
    expect(screen.queryByRole("heading", { name: /403/ })).toBeNull();
    expect(screen.getByText("AI Gen (M2)")).toBeTruthy();
  });
  it.each(["STUDENT", "INSTRUCTOR", "ADMIN"] as UserRole[])("keeps /review route (Issue #15) accessible to %s", role => {
    auth.user = user(role);
    open("/review/attempt-id");
    expect(screen.queryByRole("heading", { name: /403/ })).toBeNull();
    expect(screen.getByTestId("location").textContent).toBe("/review/attempt-id");
  });
  it("blocks instructor from admin routes", () => {
    auth.user = user("INSTRUCTOR");
    open("/admin/users");
    expect(screen.getByRole("heading", { name: /403/ })).toBeTruthy();
  });
  it("redirects anonymous visitors to login", async () => {
    auth.user = null;
    open("/profile");
    await waitFor(() => expect(screen.getByTestId("location").textContent).toBe("/login"));
  });
  it("shows loading without rendering protected content", () => {
    auth.loading = true;
    open("/profile");
    expect(screen.getByRole("status")).toBeTruthy();
    expect(screen.queryByText("an@example.com")).toBeNull();
  });
  it.each(["STUDENT", "INSTRUCTOR", "ADMIN"] as UserRole[])("chooses home for %s", async role => {
    auth.user = user(role);
    open("/");
    await waitFor(() => expect(screen.getByTestId("location").textContent).toBe(role === "STUDENT" ? "/profile" : "/instructor/parser"));
  });
});

describe("profile and logout", () => {
  it.each(["STUDENT", "INSTRUCTOR", "ADMIN"] as UserRole[])("displays profile for %s", role => {
    auth.user = user(role);
    open("/profile");
    expect(screen.getByText("an@example.com")).toBeTruthy();
    expect(screen.getByRole("img", { name: /Nguyễn Văn An/ }).textContent).toBe("VA");
    expect(screen.getByText(new RegExp(`\\(${role}\\)`))).toBeTruthy();
  });
  it("waits for logout before navigating to login", async () => {
    let finish!: () => void;
    auth.logout.mockReturnValue(new Promise<void>(resolve => { finish = resolve; }));
    open("/profile");
    fireEvent.click(screen.getAllByRole("button", { name: "Đăng xuất" })[0]);
    expect(screen.getByRole("button", { name: "Đang xử lý…" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByTestId("location").textContent).toBe("/profile");
    finish();
    await waitFor(() => expect(screen.getByTestId("location").textContent).toBe("/login"));
  });
  it("keeps profile and shows an error if logout fails", async () => {
    auth.logout.mockRejectedValue(new Error("offline"));
    open("/profile");
    fireEvent.click(screen.getAllByRole("button", { name: "Đăng xuất" })[0]);
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(screen.getByTestId("location").textContent).toBe("/profile");
  });
});
