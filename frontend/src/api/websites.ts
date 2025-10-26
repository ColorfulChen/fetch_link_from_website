import { http } from "@/utils/http";

/** 网站数据 */
export type Website = {
  id: string;
  name: string;
  url: string;
  domain: string;
  status: "active" | "inactive";
  crawl_depth: number;
  max_links: number;
  created_at: string;
  updated_at: string;
};

/** 分页信息 */
export type Pagination = {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

/** 网站列表响应 */
export type WebsiteListResult = {
  success: boolean;
  data: Array<Website>;
  pagination: Pagination;
};

/** 网站详情响应 */
export type WebsiteDetailResult = {
  success: boolean;
  data: Website;
};

/** 网站操作响应 */
export type WebsiteOperationResult = {
  success: boolean;
  message: string;
  data?: Website;
};

/** 创建网站请求参数 */
export type CreateWebsiteParams = {
  name: string;
  url: string;
  crawl_depth?: number;
  max_links?: number;
};

/** 更新网站请求参数 */
export type UpdateWebsiteParams = {
  name?: string;
  status?: "active" | "inactive";
  crawl_depth?: number;
  max_links?: number;
};

/** 获取网站列表查询参数 */
export type GetWebsitesParams = {
  status?: "active" | "inactive";
  page?: number;
  page_size?: number;
};

/** 创建网站 */
export const createWebsite = (data: CreateWebsiteParams) => {
  return http.request<WebsiteOperationResult>("post", "/websites", { data });
};

/** 获取网站列表 */
export const getWebsites = (params?: GetWebsitesParams) => {
  return http.request<WebsiteListResult>("get", "/websites", { params });
};

/** 获取网站详情 */
export const getWebsiteDetail = (websiteId: string) => {
  return http.request<WebsiteDetailResult>("get", `/websites/${websiteId}`);
};

/** 更新网站 */
export const updateWebsite = (websiteId: string, data: UpdateWebsiteParams) => {
  return http.request<WebsiteOperationResult>("put", `/websites/${websiteId}`, {
    data
  });
};

/** 删除网站 */
export const deleteWebsite = (websiteId: string) => {
  return http.request<WebsiteOperationResult>(
    "delete",
    `/websites/${websiteId}`
  );
};
