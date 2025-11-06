<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Picture as IconPicture } from "@element-plus/icons-vue";
import {
  getTaskDetail,
  getTaskLogs,
  type CrawlTask,
  type TaskLog
} from "@/api/tasks";
import { formatTime } from "@/utils/time";

defineOptions({
  name: "TaskDetail"
});

const route = useRoute();
const router = useRouter();

// 任务详情
const loading = ref(false);
const taskDetail = ref<CrawlTask | null>(null);

// 日志数据
const logsLoading = ref(false);
const logs = ref<TaskLog[]>([]);
const logsTotal = ref(0);

// 日志查询参数
const logsQuery = reactive<{
  level: "" | "INFO" | "WARNING" | "ERROR";
  page: number;
  page_size: number;
}>({
  level: "",
  page: 1,
  page_size: 50
});

// 获取任务ID
const taskId = route.params.id as string;

// 状态标签类型
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: "info",
    running: "warning",
    completed: "success",
    failed: "danger"
  };
  return map[status] || "info";
};

// 日志级别类型
const getLogLevelType = (level: string) => {
  const map: Record<string, any> = {
    INFO: "info",
    WARNING: "warning",
    ERROR: "danger"
  };
  return map[level] || "info";
};

// 格式化百分比
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`;
};

// 加载任务详情
const loadTaskDetail = async () => {
  loading.value = true;
  try {
    const res = await getTaskDetail(taskId);
    if (res.success) {
      taskDetail.value = res.data;
    }
  } catch (error) {
    ElMessage.error("加载任务详情失败");
  } finally {
    loading.value = false;
  }
};

// 加载任务日志
const loadLogs = async () => {
  logsLoading.value = true;
  try {
    const res = await getTaskLogs(taskId, logsQuery);
    if (res.success) {
      logs.value = res.data;
      logsTotal.value = res.pagination.total;
    }
  } catch (error) {
    ElMessage.error("加载任务日志失败");
  } finally {
    logsLoading.value = false;
  }
};

// 返回列表
const handleBack = () => {
  router.back();
};

// 日志分页改变
const handleLogsPageChange = (page: number) => {
  logsQuery.page = page;
  loadLogs();
};

// 筛选日志
const handleLogFilter = () => {
  logsQuery.page = 1;
  loadLogs();
};

onMounted(() => {
  loadTaskDetail();
  loadLogs();
});
</script>

<template>
  <div class="task-detail">
    <el-page-header @back="handleBack">
      <template #content>
        <span class="text-lg font-semibold">任务详情</span>
      </template>
    </el-page-header>

    <!-- 任务基本信息 -->
    <el-card v-loading="loading" class="mt-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-base font-semibold">基本信息</span>
          <el-tag
            v-if="taskDetail"
            :type="getStatusType(taskDetail.status)"
            size="large"
          >
            {{ taskDetail.status }}
          </el-tag>
        </div>
      </template>

      <el-descriptions v-if="taskDetail" :column="2" border>
        <el-descriptions-item label="任务ID">{{
          taskDetail.id
        }}</el-descriptions-item>
        <el-descriptions-item label="网站ID">{{
          taskDetail.website_id
        }}</el-descriptions-item>
        <el-descriptions-item label="网站名称">{{
          taskDetail.website.name
        }}</el-descriptions-item>
        <el-descriptions-item label="网站地址">{{
          taskDetail.website.url
        }}</el-descriptions-item>
        <el-descriptions-item label="任务类型">
          {{ taskDetail.task_type === "manual" ? "手动" : "定时" }}
        </el-descriptions-item>
        <el-descriptions-item label="爬取策略">
          <el-tag
            :type="
              taskDetail.strategy === 'incremental' ? 'success' : 'warning'
            "
          >
            {{ taskDetail.strategy === "incremental" ? "增量" : "全量" }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ formatTime(taskDetail.started_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="完成时间">
          {{ formatTime(taskDetail.completed_at) }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="taskDetail.error_message"
          label="错误信息"
          :span="2"
        >
          <el-text type="danger">{{ taskDetail.error_message }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 统计信息 -->
    <el-card v-if="taskDetail" class="mt-4">
      <template #header>
        <span class="text-base font-semibold">统计信息</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic
            title="总链接数"
            :value="taskDetail.statistics.total_links"
          />
        </el-col>
        <el-col :span="6">
          <el-statistic
            title="重要链接数"
            :value="taskDetail.statistics.valid_links"
            value-style="color: #67C23A"
          />
        </el-col>
        <el-col :span="6">
          <el-statistic
            title="非重要链接数"
            :value="taskDetail.statistics.invalid_links"
            value-style="color: #F56C6C"
          />
        </el-col>
        <el-col :span="6">
          <el-statistic
            title="新增链接数"
            :value="taskDetail.statistics.new_links"
            value-style="color: #409EFF"
          />
        </el-col>
      </el-row>

      <el-divider />

      <el-row :gutter="20">
        <el-col :span="12">
          <el-statistic
            title="有效率"
            :value="taskDetail.statistics.valid_rate * 100"
            :precision="2"
            suffix="%"
          />
        </el-col>
        <el-col :span="12">
          <el-statistic
            title="精准率"
            :value="taskDetail.statistics.precision_rate * 100"
            :precision="2"
            suffix="%"
          />
        </el-col>
      </el-row>
    </el-card>

    <!-- 网站截图 -->
    <el-card v-if="taskDetail && taskDetail.screenshot_path" class="mt-4">
      <template #header>
        <span class="text-base font-semibold">网站截图</span>
      </template>

      <div class="screenshot-container">
        <el-image
          :src="`/api/screenshots/${taskDetail.screenshot_path}`"
          :preview-src-list="[`/api/screenshots/${taskDetail.screenshot_path}`]"
          fit="contain"
          style="max-width: 100%; max-height: 600px"
          lazy
        >
          <template #error>
            <div class="image-slot">
              <el-icon><icon-picture /></el-icon>
              <span>截图加载失败</span>
            </div>
          </template>
        </el-image>
      </div>
    </el-card>

    <!-- 任务日志 -->
    <el-card class="mt-4">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-base font-semibold">任务日志</span>
          <el-select
            v-model="logsQuery.level"
            placeholder="筛选日志级别"
            clearable
            style="width: 150px"
            @change="handleLogFilter"
          >
            <el-option label="INFO" value="INFO" />
            <el-option label="WARNING" value="WARNING" />
            <el-option label="ERROR" value="ERROR" />
          </el-select>
        </div>
      </template>

      <el-table v-loading="logsLoading" :data="logs" stripe max-height="500">
        <el-table-column prop="level" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getLogLevelType(row.level)" size="small">
              {{ row.level }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column
          prop="message"
          label="消息"
          min-width="400"
          show-overflow-tooltip
        />
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="logsQuery.page"
          :page-size="logsQuery.page_size"
          :total="logsTotal"
          layout="total, prev, pager, next, jumper"
          @current-change="handleLogsPageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.task-detail {
  padding: 20px;
}

.screenshot-container {
  display: flex;
  justify-content: center;
  align-items: center;

  .image-slot {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 200px;
    background: var(--el-fill-color-light);
    color: var(--el-text-color-secondary);
    font-size: 14px;

    .el-icon {
      font-size: 30px;
      margin-bottom: 10px;
    }
  }
}
</style>
