<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { ElMessage } from "element-plus";
import { getStatistics, type StatisticsSummary } from "@/api/statistics";
import { getWebsites, type Website } from "@/api/websites";

defineOptions({
  name: "Statistics"
});

// 网站列表
const websiteList = ref<Website[]>([]);

// 查询表单
const queryForm = reactive({
  website_id: "",
  date_from: "",
  date_to: ""
});

// 统计数据
const loading = ref(false);
const statistics = ref<{
  website: { id: string; name: string };
  period: { from: string; to: string };
  summary: StatisticsSummary;
} | null>(null);

// 快捷日期选择
const shortcuts = [
  {
    text: "最近7天",
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 7);
      return [start, end];
    }
  },
  {
    text: "最近30天",
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setDate(start.getDate() - 30);
      return [start, end];
    }
  },
  {
    text: "最近3个月",
    value: () => {
      const end = new Date();
      const start = new Date();
      start.setMonth(start.getMonth() - 3);
      return [start, end];
    }
  }
];

// 加载网站列表
const loadWebsites = async () => {
  try {
    const res = await getWebsites({ status: "active" });
    if (res.success) {
      websiteList.value = res.data;
      // 默认选择第一个网站
      if (res.data.length > 0) {
        queryForm.website_id = res.data[0].id;
        loadStatistics();
      }
    }
  } catch (error) {
    console.error("加载网站列表失败", error);
  }
};

// 加载统计数据
const loadStatistics = async () => {
  if (!queryForm.website_id) {
    ElMessage.warning("请选择网站");
    return;
  }

  loading.value = true;
  try {
    const res = await getStatistics(queryForm);
    if (res.success) {
      statistics.value = res.data;
    }
  } catch (error) {
    ElMessage.error("加载统计数据失败");
  } finally {
    loading.value = false;
  }
};

// 查询
const handleQuery = () => {
  loadStatistics();
};

// 重置
const handleReset = () => {
  queryForm.date_from = "";
  queryForm.date_to = "";
  loadStatistics();
};

// 格式化百分比
const formatPercent = (value: number) => {
  return `${(value * 100).toFixed(2)}%`;
};

// 格式化进度条百分比显示
const formatProgressPercent = (percentage: number) => {
  return `${percentage.toFixed(2)}%`;
};

onMounted(() => {
  loadWebsites();
});
</script>

<template>
  <div class="statistics">
    <!-- 查询表单 -->
    <el-card class="mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <span class="text-sm whitespace-nowrap">网站</span>
          <el-select
            v-model="queryForm.website_id"
            placeholder="请选择网站"
            style="width: 200px"
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
          <span class="text-sm whitespace-nowrap">日期范围</span>
          <el-date-picker
            v-model="queryForm.date_from"
            type="date"
            placeholder="开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="shortcuts"
            style="width: 150px"
          />
          <span class="text-sm text-gray-500">至</span>
          <el-date-picker
            v-model="queryForm.date_to"
            type="date"
            placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="shortcuts"
            style="width: 150px"
          />
        </div>
        <div class="flex items-center gap-2">
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计概览 -->
    <el-card v-if="statistics" v-loading="loading">
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-base font-semibold"
            >统计概览 - {{ statistics.website.name }}</span
          >
          <el-text type="info" size="small">
            统计周期: {{ statistics.period.from }} ~ {{ statistics.period.to }}
          </el-text>
        </div>
      </template>

      <!-- 任务统计 -->
      <div class="mb-6">
        <el-divider content-position="left">
          <span class="text-base font-semibold">任务统计</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic
              title="总任务数"
              :value="statistics.summary.total_tasks"
              value-style="color: #409EFF"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="已完成任务"
              :value="statistics.summary.completed_tasks"
              value-style="color: #67C23A"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="失败任务"
              :value="statistics.summary.failed_tasks"
              value-style="color: #F56C6C"
            />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="任务成功率"
              :value="
                statistics.summary.total_tasks > 0
                  ? formatPercent(
                      statistics.summary.completed_tasks /
                        statistics.summary.total_tasks
                    )
                  : '0%'
              "
              value-style="color: #67C23A"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 链接统计 -->
      <div class="mb-6">
        <el-divider content-position="left">
          <span class="text-base font-semibold">链接统计</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic
              title="总爬取链接数"
              :value="statistics.summary.total_links_crawled"
              value-style="color: #409EFF"
            />
          </el-col>
          <el-col :span="8">
            <el-statistic
              title="新增链接数"
              :value="statistics.summary.new_links_found"
              value-style="color: #E6A23C"
            />
          </el-col>
          <el-col :span="8">
            <el-statistic
              title="平均新增率"
              :value="
                statistics.summary.total_links_crawled > 0
                  ? formatPercent(
                      statistics.summary.new_links_found /
                        statistics.summary.total_links_crawled
                    )
                  : '0%'
              "
              value-style="color: #E6A23C"
            />
          </el-col>
        </el-row>
      </div>

      <!-- 质量统计 -->
      <div>
        <el-divider content-position="left">
          <span class="text-base font-semibold">质量统计</span>
        </el-divider>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card shadow="never" class="text-center">
              <el-statistic
                title="重要链接比例"
                :value="formatPercent(statistics.summary.avg_valid_rate)"
                value-style="color: #67C23A; font-size: 32px"
              />
              <el-progress
                :percentage="statistics.summary.avg_valid_rate * 100"
                :stroke-width="20"
                :format="formatProgressPercent"
                class="mt-4"
              />
              <el-text type="info" size="small" class="mt-2">
                重要链接占总连接的比例
              </el-text>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" class="text-center">
              <el-statistic
                title="平均精准率"
                :value="formatPercent(statistics.summary.avg_precision_rate)"
                value-style="color: #409EFF; font-size: 32px"
              />
              <el-progress
                :percentage="statistics.summary.avg_precision_rate * 100"
                :stroke-width="20"
                :format="formatProgressPercent"
                color="#409EFF"
                class="mt-4"
              />
              <el-text type="info" size="small" class="mt-2">
                重要链接识别准确率
              </el-text>
            </el-card>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else-if="!loading" description="请选择网站查看统计数据" />
  </div>
</template>

<style scoped lang="scss">
.statistics {
  padding: 20px;
}
</style>
