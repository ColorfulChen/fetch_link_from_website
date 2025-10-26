import { http } from "@/utils/http";

/** 调度任务数据 */
export type Schedule = {
  id: string;
  website_id: string;
  name: string;
  schedule_type: "hourly" | "daily" | "monthly";
  cron_expression: string;
  strategy: "incremental" | "full";
  is_active: boolean;
  next_run_time: string | null;
  last_run_time: string | null;
  created_at: string;
};

/** 调度列表响应 */
export type ScheduleListResult = {
  success: boolean;
  data: Array<Schedule>;
};

/** 调度操作响应 */
export type ScheduleOperationResult = {
  success: boolean;
  message: string;
  data?: Schedule;
};

/** 创建调度请求参数 */
export type CreateScheduleParams = {
  website_id: string;
  name: string;
  schedule_type: "hourly" | "daily" | "monthly";
  strategy?: "incremental" | "full";
  hour?: number;
  day?: number;
};

/** 更新调度请求参数 */
export type UpdateScheduleParams = {
  is_active: boolean;
};

/** 获取调度列表查询参数 */
export type GetSchedulesParams = {
  website_id?: string;
};

/** 创建调度任务 */
export const createSchedule = (data: CreateScheduleParams) => {
  return http.request<ScheduleOperationResult>("post", "/schedules", { data });
};

/** 获取调度列表 */
export const getSchedules = (params?: GetSchedulesParams) => {
  return http.request<ScheduleListResult>("get", "/schedules", { params });
};

/** 更新调度状态 */
export const updateSchedule = (
  scheduleId: string,
  data: UpdateScheduleParams
) => {
  return http.request<ScheduleOperationResult>(
    "patch",
    `/schedules/${scheduleId}`,
    { data }
  );
};

/** 删除调度 */
export const deleteSchedule = (scheduleId: string) => {
  return http.request<ScheduleOperationResult>(
    "delete",
    `/schedules/${scheduleId}`
  );
};
