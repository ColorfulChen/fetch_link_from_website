import { http } from "@/utils/http";

/** 导出过滤条件 */
export type ExportFilters = {
  link_type?: "valid" | "invalid";
  domain?: string;
};

/** 导出数据响应 */
export type ExportDataResult = {
  success: boolean;
  message: string;
  data: {
    download_url: string;
    file_name: string;
    total_records: number;
    file_size: string;
  };
};

/** 导出数据请求参数 */
export type ExportDataParams = {
  website_id: string;
  export_type: "incremental" | "full";
  format?: "csv" | "json";
  since_date?: string;
  filters?: ExportFilters;
};

/** 批量导出数据请求参数 */
export type BatchExportDataParams = {
  website_ids: string[];
  export_type: "incremental" | "full";
  format?: "csv" | "json";
  since_date?: string;
  filters?: ExportFilters;
};

/** 批量导出数据响应 */
export type BatchExportDataResult = {
  success: boolean;
  message: string;
  data: {
    download_url: string;
    file_name: string;
    total_records: number;
    file_size: string;
    website_count: number;
  };
};

/** 导出数据 */
export const exportData = (data: ExportDataParams) => {
  return http.request<ExportDataResult>("post", "/export", { data });
};

/** 批量导出数据 */
export const batchExportData = (data: BatchExportDataParams) => {
  return http.request<BatchExportDataResult>("post", "/export/batch", { data });
};

/** 下载导出文件 */
export const downloadExportFile = (filename: string) => {
  // 直接返回下载 URL,由浏览器处理下载
  return `/api/export/download/${filename}`;
};
