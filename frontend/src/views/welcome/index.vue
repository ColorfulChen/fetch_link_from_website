<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { ElMessage } from "element-plus";
import { getAllStatistics, type StatisticsSummary } from "@/api/statistics";

defineOptions({
  name: "Welcome"
});

// 查询表单
const queryForm = reactive({
  date_from: "",
  date_to: ""
});

// 统计数据
const loading = ref(false);
const statistics = ref<{
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

// 加载统计数据
const loadStatistics = async () => {
  loading.value = true;
  try {
    const res = await getAllStatistics(queryForm);
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

onMounted(() => {
  loadStatistics();
});
</script>

<template>
  <div class="welcome">
    <!-- 欢迎标题 -->
    <el-card class="mb-4">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">
          欢迎使用 链接重要性评估系统
        </h1>
        <p class="text-gray-500">网页链接爬虫系统</p>
      </div>
    </el-card>

    <!-- 查询表单 -->
    <el-card class="mb-4">
      <div class="flex flex-wrap items-center gap-4">
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
          <span class="text-base font-semibold">所有网站统计概览</span>
          <el-text type="info" size="small">
            统计周期: {{ statistics.period.from || "全部" }} ~
            {{ statistics.period.to || "全部" }}
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
            <div class="text-center">
              <div class="text-gray-500 text-sm mb-2">任务成功率</div>
              <div class="text-2xl font-semibold" style="color: #67c23a">
                {{
                  statistics.summary.total_tasks > 0
                    ? formatPercent(
                        statistics.summary.completed_tasks /
                          statistics.summary.total_tasks
                      )
                    : "0%"
                }}
              </div>
            </div>
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
            <div class="text-center">
              <div class="text-gray-500 text-sm mb-2">平均新增率</div>
              <div class="text-2xl font-semibold" style="color: #e6a23c">
                {{
                  statistics.summary.total_links_crawled > 0
                    ? formatPercent(
                        statistics.summary.new_links_found /
                          statistics.summary.total_links_crawled
                      )
                    : "0%"
                }}
              </div>
            </div>
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
              <div class="mb-4">
                <div class="text-gray-500 text-sm mb-2">重要链接占比</div>
                <div class="text-4xl font-semibold" style="color: #67c23a">
                  {{ formatPercent(statistics.summary.avg_valid_rate) }}
                </div>
              </div>
              <el-progress
                :percentage="statistics.summary.avg_valid_rate * 100"
                :stroke-width="20"
                class="mt-4"
              />
              <el-text type="info" size="small" class="mt-2">
                重要链接占总连接的比例
              </el-text>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never" class="text-center">
              <div class="mb-4">
                <div class="text-gray-500 text-sm mb-2">平均精准率</div>
                <div class="text-4xl font-semibold" style="color: #409eff">
                  {{ formatPercent(statistics.summary.avg_precision_rate) }}
                </div>
              </div>
              <el-progress
                :percentage="statistics.summary.avg_precision_rate * 100"
                :stroke-width="20"
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
    <el-empty v-else-if="!loading" description="暂无统计数据" />
  </div>
</template>

<style scoped lang="scss">
.welcome {
  padding: 20px;
}
</style>
