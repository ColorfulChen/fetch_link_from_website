<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  getTasks,
  createCrawlTask,
  cancelTask,
  deleteTask,
  type CrawlTask,
  type CreateCrawlTaskParams
} from "@/api/tasks";
import { getWebsites, type Website } from "@/api/websites";
import { formatTime } from "@/utils/time";

defineOptions({
  name: "TaskManage"
});

const router = useRouter();

// 表格数据
const loading = ref(false);
const tableData = ref<CrawlTask[]>([]);
const total = ref(0);

// 网站列表
const websiteList = ref<Website[]>([]);

// 查询参数
const queryForm = reactive({
  website_id: "",
  status: "",
  page: 1,
  page_size: 20
});

// 创建任务对话框
const dialogVisible = ref(false);
const formRef = ref();
const form = reactive<CreateCrawlTaskParams>({
  website_id: "",
  strategy: "incremental",
  depth: 3,
  max_links: 1000
});

// 表单验证规则
const rules = {
  website_id: [{ required: true, message: "请选择网站", trigger: "change" }],
  strategy: [{ required: true, message: "请选择策略", trigger: "change" }]
};

// 状态标签类型
const getStatusType = (status: string) => {
  const map: Record<string, any> = {
    pending: "info",
    running: "warning",
    completed: "success",
    failed: "danger",
    cancelled: ""
  };
  return map[status] || "info";
};

// 状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: "等待中",
    running: "运行中",
    completed: "已完成",
    failed: "失败",
    cancelled: "已取消"
  };
  return map[status] || status;
};

// 策略文本
const getStrategyText = (strategy: string) => {
  return strategy === "incremental" ? "增量" : "全量";
};

// 加载网站列表
const loadWebsites = async () => {
  try {
    const res = await getWebsites({ status: "active" });
    if (res.success) {
      websiteList.value = res.data;
    }
  } catch (error) {
    console.error("加载网站列表失败", error);
  }
};

// 加载任务列表
const loadTasks = async () => {
  loading.value = true;
  try {
    const res = await getTasks(queryForm);
    if (res.success) {
      tableData.value = res.data;
      total.value = res.pagination.total;
    }
  } catch (error) {
    ElMessage.error("加载任务列表失败");
  } finally {
    loading.value = false;
  }
};

// 打开创建对话框
const handleCreate = () => {
  Object.assign(form, {
    website_id: "",
    strategy: "incremental",
    depth: 3,
    max_links: 1000
  });
  dialogVisible.value = true;
};

// 提交创建表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    try {
      await createCrawlTask(form);
      ElMessage.success("爬取任务已创建");
      dialogVisible.value = false;
      loadTasks();
    } catch (error: any) {
      ElMessage.error(error.message || "创建任务失败");
    }
  });
};

// 查看详情
const handleViewDetail = (row: CrawlTask) => {
  router.push(`/crawler/tasks/${row.id}`);
};

// 格式化百分比
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`;
};

// 分页改变
const handlePageChange = (page: number) => {
  queryForm.page = page;
  loadTasks();
};

// 查询
const handleQuery = () => {
  queryForm.page = 1;
  loadTasks();
};

// 重置
const handleReset = () => {
  queryForm.website_id = "";
  queryForm.status = "";
  queryForm.page = 1;
  loadTasks();
};

// 取消任务
const handleCancel = (row: CrawlTask) => {
  ElMessageBox.confirm(
    `确定要取消任务"${row.id}"吗？任务将在下一个检查点停止。`,
    "提示",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }
  )
    .then(async () => {
      try {
        await cancelTask(row.id);
        ElMessage.success("任务取消请求已发送");
        loadTasks();
      } catch (error) {
        // HTTP 拦截器已经显示了错误信息
      }
    })
    .catch(() => {});
};

// 删除任务
const handleDelete = (row: CrawlTask) => {
  ElMessageBox.confirm(
    `确定要删除任务"${row.id}"吗？此操作将同时删除任务的所有日志记录。`,
    "提示",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    }
  )
    .then(async () => {
      try {
        await deleteTask(row.id);
        ElMessage.success("任务已删除");
        loadTasks();
      } catch (error) {
        // HTTP 拦截器已经显示了错误信息
      }
    })
    .catch(() => {});
};

onMounted(() => {
  loadWebsites();
  loadTasks();
});
</script>

<template>
  <div class="task-manage">
    <!-- 查询表单 -->
    <el-card class="mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <span class="text-sm whitespace-nowrap">网站</span>
          <el-select
            v-model="queryForm.website_id"
            placeholder="请选择网站"
            style="width: 200px"
            clearable
          >
            <el-option
              v-for="website in websiteList"
              :key="website.id"
              :label="website.name"
              :value="website.id"
            />
          </el-select>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm whitespace-nowrap">状态</span>
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            style="width: 150px"
            clearable
          >
            <el-option label="等待中" value="pending" />
            <el-option label="运行中" value="running" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </div>
        <div class="flex items-center gap-2">
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">创建任务</el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column
          prop="website.name"
          label="网站"
          width="150"
          show-overflow-tooltip
        />
        <el-table-column prop="task_type" label="类型" width="80">
          <template #default="{ row }">
            {{ row.task_type === "manual" ? "手动" : "定时" }}
          </template>
        </el-table-column>
        <el-table-column prop="strategy" label="策略" width="80">
          <template #default="{ row }">
            <el-tag
              :type="row.strategy === 'incremental' ? 'success' : 'warning'"
              size="small"
            >
              {{ getStrategyText(row.strategy) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="统计" min-width="200">
          <template #default="{ row }">
            <div class="text-sm">
              <div>总链接: {{ row.statistics.total_links }}</div>
              <div>新增: {{ row.statistics.new_links }}</div>
              <div>有效率: {{ formatPercent(row.statistics.valid_rate) }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.started_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="completed_at" label="完成时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.completed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewDetail(row)"
            >
              查看详情
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              type="warning"
              size="small"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status !== 'running'"
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="queryForm.page"
          :page-size="queryForm.page_size"
          :total="total"
          layout="total, prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建爬取任务"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="选择网站" prop="website_id">
          <el-select
            v-model="form.website_id"
            placeholder="请选择网站"
            style="width: 100%"
          >
            <el-option
              v-for="website in websiteList"
              :key="website.id"
              :label="website.name"
              :value="website.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="爬取策略" prop="strategy">
          <el-radio-group v-model="form.strategy">
            <el-radio label="incremental">增量爬取（仅爬取新链接）</el-radio>
            <el-radio label="full">全量爬取（重新爬取所有链接）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="爬取深度">
          <el-input-number
            v-model="form.depth"
            :min="1"
            :max="10"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="最大链接数">
          <el-input-number
            v-model="form.max_links"
            :min="100"
            :max="100000"
            :step="100"
            controls-position="right"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped lang="scss">
.task-manage {
  padding: 20px;
}
</style>
