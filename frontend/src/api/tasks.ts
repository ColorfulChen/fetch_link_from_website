import { http } from "@/utils/http";
import type { Pagination } from "./websites";

/** 任务统计数据 */
export type TaskStatistics = {
  total_links: number;
  valid_links: number;
  invalid_links: number;
  new_links: number;
  valid_rate: number;
  precision_rate: number;
};

/** 爬取任务数据 */
export type CrawlTask = {
  id: string;
  website_id: string;
  task_type: "manual" | "scheduled";
  strategy: "incremental" | "full";
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  started_at: string | null;
  completed_at: string | null;
  statistics: TaskStatistics;
  error_message: string | null;
};

/** 任务日志数据 */
export type TaskLog = {
  id: string;
  task_id: string;
  level: "INFO" | "WARNING" | "ERROR";
  message: string;
  details: Record<string, any>;
  created_at: string;
};

/** 任务列表响应 */
export type TaskListResult = {
  success: boolean;
  data: Array<CrawlTask>;
  pagination: Pagination;
};

/** 任务详情响应 */
export type TaskDetailResult = {
  success: boolean;
  data: CrawlTask;
};

/** 任务日志响应 */
export type TaskLogsResult = {
  success: boolean;
  data: Array<TaskLog>;
  pagination: Pagination;
};

/** 创建任务响应 */
export type CreateTaskResult = {
  success: boolean;
  message: string;
  data: CrawlTask;
};

/** 创建爬取任务请求参数 */
export type CreateCrawlTaskParams = {
  website_id: string;
  strategy: "incremental" | "full";
  depth?: number;
  max_links?: number;
};

/** 获取任务列表查询参数 */
export type GetTasksParams = {
  website_id?: string;
  status?: "pending" | "running" | "completed" | "failed" | "cancelled";
  page?: number;
  page_size?: number;
};

/** 获取任务日志查询参数 */
export type GetTaskLogsParams = {
  level?: "INFO" | "WARNING" | "ERROR";
  page?: number;
  page_size?: number;
};

/** 创建爬取任务 */
export const createCrawlTask = (data: CreateCrawlTaskParams) => {
  return http.request<CreateTaskResult>("post", "/tasks/crawl", { data });
};

/** 获取任务列表 */
export const getTasks = (params?: GetTasksParams) => {
  return http.request<TaskListResult>("get", "/tasks", { params });
};

/** 获取任务详情 */
export const getTaskDetail = (taskId: string) => {
  return http.request<TaskDetailResult>("get", `/tasks/${taskId}`);
};

/** 获取任务日志 */
export const getTaskLogs = (taskId: string, params?: GetTaskLogsParams) => {
  return http.request<TaskLogsResult>("get", `/tasks/${taskId}/logs`, {
    params
  });
};

/** 取消任务响应 */
export type CancelTaskResult = {
  success: boolean;
  message: string;
  data: {
    task_id: string;
    status: string;
  };
};

/** 删除任务响应 */
export type DeleteTaskResult = {
  success: boolean;
  message: string;
  data: {
    task_id: string;
  };
};

/** 取消运行中的任务 */
export const cancelTask = (taskId: string) => {
  return http.request<CancelTaskResult>("post", `/tasks/${taskId}/cancel`);
};

/** 删除任务 */
export const deleteTask = (taskId: string) => {
  return http.request<DeleteTaskResult>("delete", `/tasks/${taskId}`);
};
