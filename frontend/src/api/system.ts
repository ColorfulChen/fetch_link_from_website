import { http } from "@/utils/http";

/** 系统信息响应 */
export type SystemInfoResult = {
  message: string;
  version: string;
  endpoints: {
    health: string;
    websites: string;
    tasks: string;
    schedules: string;
    export: string;
    statistics: string;
  };
};

/** 健康检查响应 */
export type HealthCheckResult = {
  status: "healthy" | "unhealthy";
  database: "connected" | "disconnected";
  message: string;
};

/** 获取系统信息 */
export const getSystemInfo = () => {
  return http.request<SystemInfoResult>("get", "/");
};

/** 健康检查 */
export const healthCheck = () => {
  return http.request<HealthCheckResult>("get", "/health");
};
