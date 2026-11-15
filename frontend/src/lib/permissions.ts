import { UserRole } from "@/types";

export const instructorRoles: UserRole[] = ["INSTRUCTOR", "ADMIN"];
export const roleLabels: Record<UserRole, string> = {
  STUDENT: "Sinh viên", INSTRUCTOR: "Giảng viên", ADMIN: "Quản trị viên",
};
export const canManageExams = (role: UserRole) => instructorRoles.includes(role);
export const homePath = (role: UserRole) => canManageExams(role) ? "/instructor/parser" : "/profile";
