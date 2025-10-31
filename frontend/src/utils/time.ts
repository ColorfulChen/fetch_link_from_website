/**
 * 时间格式化工具函数
 * 将 UTC 时间转换为 UTC+8 时区显示
 */

/**
 * 格式化时间为 UTC+8 时区
 * @param time - ISO 格式的时间字符串或 null
 * @param format - 格式化选项，默认为完整日期时间
 * @returns 格式化后的时间字符串，如果输入为空则返回 "-"
 */
export function formatTime(
  time: string | null | undefined,
  format: "datetime" | "date" | "time" = "datetime"
): string {
  if (!time) return "-";

  try {
    // 创建 Date 对象（自动解析为本地时间）
    const date = new Date(time);

    // 手动加 8 小时转换为 UTC+8
    const utc8Date = new Date(date.getTime() + 8 * 60 * 60 * 1000);

    // 根据格式选项返回不同的格式
    switch (format) {
      case "date":
        return utc8Date.toLocaleDateString("zh-CN", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
        });
      case "time":
        return utc8Date.toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false
        });
      case "datetime":
      default:
        return utc8Date.toLocaleString("zh-CN", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false
        });
    }
  } catch (error) {
    console.error("时间格式化错误:", error);
    return "-";
  }
}

/**
 * 格式化为相对时间（如："1小时前"、"2天前"）
 * @param time - ISO 格式的时间字符串或 null
 * @returns 相对时间字符串
 */
export function formatRelativeTime(time: string | null | undefined): string {
  if (!time) return "-";

  try {
    const date = new Date(time);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    if (years > 0) return `${years}年前`;
    if (months > 0) return `${months}个月前`;
    if (days > 0) return `${days}天前`;
    if (hours > 0) return `${hours}小时前`;
    if (minutes > 0) return `${minutes}分钟前`;
    if (seconds > 0) return `${seconds}秒前`;
    return "刚刚";
  } catch (error) {
    console.error("相对时间格式化错误:", error);
    return "-";
  }
}

/**
 * 计算时间差（返回秒数）
 * @param start - 开始时间
 * @param end - 结束时间（默认为当前时间）
 * @returns 时间差（秒）
 */
export function timeDiff(
  start: string | Date,
  end: string | Date = new Date()
): number {
  const startTime = typeof start === "string" ? new Date(start) : start;
  const endTime = typeof end === "string" ? new Date(end) : end;
  return Math.floor((endTime.getTime() - startTime.getTime()) / 1000);
}

/**
 * 格式化持续时间（如："1小时30分钟"）
 * @param seconds - 持续时间（秒）
 * @returns 格式化后的持续时间字符串
 */
export function formatDuration(seconds: number): string {
  if (seconds < 0) return "-";
  if (seconds === 0) return "0秒";

  const days = Math.floor(seconds / (24 * 60 * 60));
  const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
  const minutes = Math.floor((seconds % (60 * 60)) / 60);
  const secs = Math.floor(seconds % 60);

  const parts: string[] = [];
  if (days > 0) parts.push(`${days}天`);
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  if (secs > 0) parts.push(`${secs}秒`);

  return parts.join("");
}
