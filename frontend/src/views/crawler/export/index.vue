<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { ElMessage } from "element-plus";
import {
  exportData,
  batchExportData,
  downloadExportFile,
  type ExportDataParams,
  type BatchExportDataParams
} from "@/api/export";
import { getWebsites, type Website } from "@/api/websites";
import { formatTime } from "@/utils/time";

defineOptions({
  name: "DataExport"
});

// 导出模式：single（单个）或 batch（批量）
const exportMode = ref<"single" | "batch">("single");

// 网站列表
const websiteList = ref<Website[]>([]);

// 导出历史
const exportHistory = ref<any[]>([]);

// 单个导出表单
const formRef = ref();
const form = reactive<ExportDataParams>({
  website_id: "",
  export_type: "full",
  format: "csv",
  since_date: "",
  filters: {}
});

// 批量导出表单
const batchFormRef = ref();
const batchForm = reactive<BatchExportDataParams>({
  website_ids: [],
  export_type: "full",
  format: "csv",
  since_date: "",
  filters: {}
});

// 表单验证规则
const rules = {
  website_id: [{ required: true, message: "请选择网站", trigger: "change" }],
  export_type: [
    { required: true, message: "请选择导出类型", trigger: "change" }
  ],
  format: [{ required: true, message: "请选择导出格式", trigger: "change" }]
};

// 批量导出表单验证规则
const batchRules = {
  website_ids: [
    {
      required: true,
      message: "请至少选择一个网站",
      trigger: "change",
      validator: (rule: any, value: string[], callback: any) => {
        if (!value || value.length === 0) {
          callback(new Error("请至少选择一个网站"));
        } else {
          callback();
        }
      }
    }
  ],
  export_type: [
    { required: true, message: "请选择导出类型", trigger: "change" }
  ],
  format: [{ required: true, message: "请选择导出格式", trigger: "change" }]
};

// 导出中
const exporting = ref(false);

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

// 提交单个导出
const handleExport = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    exporting.value = true;
    try {
      const res = await exportData(form);
      if (res.success) {
        ElMessage.success("导出成功");

        // 添加到历史记录
        exportHistory.value.unshift({
          ...res.data,
          export_time: formatTime(new Date().toISOString()),
          website_name:
            websiteList.value.find(w => w.id === form.website_id)?.name || ""
        });

        // 自动下载
        const downloadUrl = downloadExportFile(res.data.file_name);
        window.open(downloadUrl, "_blank");
      }
    } catch (error: any) {
      ElMessage.error(error.message || "导出失败");
    } finally {
      exporting.value = false;
    }
  });
};

// 提交批量导出
const handleBatchExport = async () => {
  if (!batchFormRef.value) return;
  await batchFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    exporting.value = true;
    try {
      const res = await batchExportData(batchForm);
      if (res.success) {
        ElMessage.success(
          `批量导出成功，共导出 ${res.data.website_count} 个网站的数据`
        );

        // 添加到历史记录
        const websiteNames = batchForm.website_ids
          .map(id => websiteList.value.find(w => w.id === id)?.name || "")
          .filter(name => name)
          .join(", ");

        exportHistory.value.unshift({
          ...res.data,
          export_time: formatTime(new Date().toISOString()),
          website_name: `批量导出 (${res.data.website_count}个网站)`
        });

        // 自动下载
        const downloadUrl = downloadExportFile(res.data.file_name);
        window.open(downloadUrl, "_blank");
      }
    } catch (error: any) {
      ElMessage.error(error.message || "批量导出失败");
    } finally {
      exporting.value = false;
    }
  });
};

// 下载文件
const handleDownload = (filename: string) => {
  const downloadUrl = downloadExportFile(filename);
  window.open(downloadUrl, "_blank");
};

// 重置单个导出表单
const handleReset = () => {
  if (!formRef.value) return;
  formRef.value.resetFields();
};

// 重置批量导出表单
const handleBatchReset = () => {
  if (!batchFormRef.value) return;
  batchFormRef.value.resetFields();
};

onMounted(() => {
  loadWebsites();
});
</script>

<template>
  <div class="data-export">
    <!-- 导出配置 -->
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <span class="text-base font-semibold">数据导出</span>
          <el-radio-group v-model="exportMode" size="small">
            <el-radio-button label="single">单个导出</el-radio-button>
            <el-radio-button label="batch">批量导出</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 单个导出表单 -->
      <el-form
        v-if="exportMode === 'single'"
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
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

        <el-form-item label="导出类型" prop="export_type">
          <el-radio-group v-model="form.export_type">
            <el-radio label="full">全量导出（所有历史链接）</el-radio>
            <el-radio label="incremental"
              >增量导出（指定日期后的新链接）</el-radio
            >
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="form.export_type === 'incremental'"
          label="起始日期"
          prop="since_date"
        >
          <el-date-picker
            v-model="form.since_date"
            type="datetime"
            placeholder="选择起始日期"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss[Z]"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="导出格式" prop="format">
          <el-radio-group v-model="form.format">
            <el-radio label="csv">CSV 格式</el-radio>
            <el-radio label="json">JSON 格式</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="链接类型">
          <el-select
            v-model="form.filters!.link_type"
            placeholder="全部"
            clearable
            style="width: 100%"
          >
            <el-option label="重要链接" value="valid" />
            <el-option label="非重要链接" value="invalid" />
          </el-select>
        </el-form-item>

        <el-form-item label="域名过滤">
          <el-input
            v-model="form.filters!.domain"
            placeholder="输入域名进行过滤（可选）"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="exporting" @click="handleExport">
            开始导出
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 批量导出表单 -->
      <el-form
        v-else
        ref="batchFormRef"
        :model="batchForm"
        :rules="batchRules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="选择网站" prop="website_ids">
          <el-select
            v-model="batchForm.website_ids"
            placeholder="请选择网站（可多选）"
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 100%"
          >
            <el-option
              v-for="website in websiteList"
              :key="website.id"
              :label="website.name"
              :value="website.id"
            />
          </el-select>
          <div class="mt-1 text-xs text-gray-500">
            已选择 {{ batchForm.website_ids.length }} 个网站
          </div>
        </el-form-item>

        <el-form-item label="导出类型" prop="export_type">
          <el-radio-group v-model="batchForm.export_type">
            <el-radio label="full">全量导出（所有历史链接）</el-radio>
            <el-radio label="incremental"
              >增量导出（指定日期后的新链接）</el-radio
            >
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="batchForm.export_type === 'incremental'"
          label="起始日期"
          prop="since_date"
        >
          <el-date-picker
            v-model="batchForm.since_date"
            type="datetime"
            placeholder="选择起始日期"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DDTHH:mm:ss[Z]"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="导出格式" prop="format">
          <el-radio-group v-model="batchForm.format">
            <el-radio label="csv">CSV 格式</el-radio>
            <el-radio label="json">JSON 格式</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="链接类型">
          <el-select
            v-model="batchForm.filters!.link_type"
            placeholder="全部"
            clearable
            style="width: 100%"
          >
            <el-option label="重要链接" value="valid" />
            <el-option label="非重要链接" value="invalid" />
          </el-select>
        </el-form-item>

        <el-form-item label="域名过滤">
          <el-input
            v-model="batchForm.filters!.domain"
            placeholder="输入域名进行过滤（可选）"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="exporting"
            @click="handleBatchExport"
          >
            批量导出
          </el-button>
          <el-button @click="handleBatchReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 导出历史 -->
    <el-card v-if="exportHistory.length > 0" class="mt-4">
      <template #header>
        <span class="text-base font-semibold">导出历史</span>
      </template>

      <el-table :data="exportHistory" stripe>
        <el-table-column prop="website_name" label="网站" width="150" />
        <el-table-column
          prop="file_name"
          label="文件名"
          min-width="300"
          show-overflow-tooltip
        />
        <el-table-column prop="total_records" label="记录数" width="100" />
        <el-table-column prop="file_size" label="文件大小" width="120" />
        <el-table-column prop="export_time" label="导出时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleDownload(row.file_name)"
            >
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped lang="scss">
.data-export {
  padding: 20px;
}
</style>
