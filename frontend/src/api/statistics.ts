import { http } from "@/utils/http";

/** 统计摘要数据 */
export type StatisticsSummary = {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_links_crawled: number;
  new_links_found: number;
  avg_valid_rate: number;
  avg_precision_rate: number;
};

/** 统计数据响应 */
export type StatisticsResult = {
  success: boolean;
  data: {
    website: {
      id: string;
      name: string;
    };
    period: {
      from: string;
      to: string;
    };
    summary: StatisticsSummary;
  };
};

/** 获取统计数据查询参数 */
export type GetStatisticsParams = {
  website_id: string;
  date_from?: string;
  date_to?: string;
};

/** 获取统计数据 */
export const getStatistics = (params: GetStatisticsParams) => {
  return http.request<StatisticsResult>("get", "/statistics", { params });
};

/** 获取所有网站统计数据查询参数 */
export type GetAllStatisticsParams = {
  date_from?: string;
  date_to?: string;
};

/** 所有网站统计数据响应 */
export type AllStatisticsResult = {
  success: boolean;
  data: {
    period: {
      from: string;
      to: string;
    };
    summary: StatisticsSummary;
  };
};

/** 获取所有网站的统计数据 */
export const getAllStatistics = (params?: GetAllStatisticsParams) => {
  return http.request<AllStatisticsResult>("get", "/statistics/all", { params });
};
