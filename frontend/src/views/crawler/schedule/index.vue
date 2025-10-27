<script setup lang="ts">
import { ref, onMounted, reactive, computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  type Schedule,
  type CreateScheduleParams
} from "@/api/schedules";
import { getWebsites, type Website } from "@/api/websites";
import { formatTime } from "@/utils/time";

defineOptions({
  name: "ScheduleManage"
});

// 表格数据
const loading = ref(false);
const tableData = ref<Schedule[]>([]);

// 网站列表
const websiteList = ref<Website[]>([]);

// 查询参数
const queryForm = reactive({
  website_id: ""
});

// 对话框
const dialogVisible = ref(false);
const formRef = ref();
const form = reactive<CreateScheduleParams>({
  website_id: "",
  name: "",
  schedule_type: "daily",
  strategy: "incremental",
  hour: 2,
  day: 1
});

// 表单验证规则
const rules = computed(() => ({
  website_id: [{ required: true, message: "请选择网站", trigger: "change" }],
  name: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  schedule_type: [
    { required: true, message: "请选择调度类型", trigger: "change" }
  ],
  strategy: [{ required: true, message: "请选择爬取策略", trigger: "change" }],
  hour: [
    {
      required:
        form.schedule_type === "daily" || form.schedule_type === "monthly",
      message: "请输入小时",
      trigger: "blur"
    }
  ],
  day: [
    {
      required: form.schedule_type === "monthly",
      message: "请输入日期",
      trigger: "blur"
    }
  ]
}));

// 调度类型文本
const getScheduleTypeText = (type: string) => {
  const map: Record<string, string> = {
    hourly: "每小时",
    daily: "每天",
    monthly: "每月"
  };
  return map[type] || type;
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

// 加载调度列表
const loadSchedules = async () => {
  loading.value = true;
  try {
    const res = await getSchedules(queryForm);
    if (res.success) {
      tableData.value = res.data;
    }
  } catch (error) {
    ElMessage.error("加载调度列表失败");
  } finally {
    loading.value = false;
  }
};

// 打开创建对话框
const handleCreate = () => {
  Object.assign(form, {
    website_id: "",
    name: "",
    schedule_type: "daily",
    strategy: "incremental",
    hour: 2,
    day: 1
  });
  dialogVisible.value = true;
};

// 提交创建表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    try {
      await createSchedule(form);
      ElMessage.success("调度任务已创建");
      dialogVisible.value = false;
      loadSchedules();
    } catch (error: any) {
      ElMessage.error(error.message || "创建调度失败");
    }
  });
};

// 切换激活状态
const handleToggleActive = async (row: Schedule) => {
  try {
    await updateSchedule(row.id, { is_active: !row.is_active });
    ElMessage.success("状态更新成功");
    loadSchedules();
  } catch (error) {
    ElMessage.error("状态更新失败");
  }
};

// 删除调度
const handleDelete = (row: Schedule) => {
  ElMessageBox.confirm(`确定要删除调度"${row.name}"吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  })
    .then(async () => {
      try {
        await deleteSchedule(row.id);
        ElMessage.success("删除成功");
        loadSchedules();
      } catch (error) {
        ElMessage.error("删除失败");
      }
    })
    .catch(() => {});
};

// 查询
const handleQuery = () => {
  loadSchedules();
};

// 重置
const handleReset = () => {
  queryForm.website_id = "";
  loadSchedules();
};

onMounted(() => {
  loadWebsites();
  loadSchedules();
});
</script>

<template>
  <div class="schedule-manage">
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
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">创建调度</el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="schedule_type" label="调度类型" width="100">
          <template #default="{ row }">
            {{ getScheduleTypeText(row.schedule_type) }}
          </template>
        </el-table-column>
        <el-table-column
          prop="cron_expression"
          label="Cron表达式"
          width="150"
        />
        <el-table-column prop="strategy" label="爬取策略" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.strategy === 'incremental' ? 'success' : 'warning'"
              size="small"
            >
              {{ row.strategy === "incremental" ? "增量" : "全量" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? "激活" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="next_run_time" label="下次执行时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.next_run_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_run_time" label="上次执行时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_run_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              size="small"
              @click="handleToggleActive(row)"
            >
              {{ row.is_active ? "停用" : "激活" }}
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建调度对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建调度任务"
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
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="调度类型" prop="schedule_type">
          <el-radio-group v-model="form.schedule_type">
            <el-radio label="hourly">每小时</el-radio>
            <el-radio label="daily">每天</el-radio>
            <el-radio label="monthly">每月</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="
            form.schedule_type === 'daily' || form.schedule_type === 'monthly'
          "
          label="小时"
          prop="hour"
        >
          <el-input-number
            v-model="form.hour"
            :min="0"
            :max="23"
            controls-position="right"
          />
          <span class="ml-2 text-gray-500">点</span>
        </el-form-item>
        <el-form-item
          v-if="form.schedule_type === 'monthly'"
          label="日期"
          prop="day"
        >
          <el-input-number
            v-model="form.day"
            :min="1"
            :max="31"
            controls-position="right"
          />
          <span class="ml-2 text-gray-500">号</span>
        </el-form-item>
        <el-form-item label="爬取策略" prop="strategy">
          <el-radio-group v-model="form.strategy">
            <el-radio label="incremental">增量爬取</el-radio>
            <el-radio label="full">全量爬取</el-radio>
          </el-radio-group>
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
.schedule-manage {
  padding: 20px;
}
</style>
