<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { ElMessage } from "element-plus";
import {
  exportData,
  downloadExportFile,
  type ExportDataParams
} from "@/api/export";
import { getWebsites, type Website } from "@/api/websites";

defineOptions({
  name: "DataExport"
});

// 网站列表
const websiteList = ref<Website[]>([]);

// 导出历史
const exportHistory = ref<any[]>([]);

// 表单
const formRef = ref();
const form = reactive<ExportDataParams>({
  website_id: "",
  export_type: "full",
  format: "csv",
  since_date: "",
  filters: {}
});

// 表单验证规则
const rules = {
  website_id: [{ required: true, message: "请选择网站", trigger: "change" }],
  export_type: [{ required: true, message: "请选择导出类型", trigger: "change" }],
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

// 提交导出
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
          export_time: new Date().toLocaleString(),
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

// 下载文件
const handleDownload = (filename: string) => {
  const downloadUrl = downloadExportFile(filename);
  window.open(downloadUrl, "_blank");
};

// 重置表单
const handleReset = () => {
  if (!formRef.value) return;
  formRef.value.resetFields();
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
        <span class="text-base font-semibold">数据导出</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 600px"
      >
        <el-form-item label="选择网站" prop="website_id">
          <el-select v-model="form.website_id" placeholder="请选择网站" style="width: 100%">
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
            <el-radio label="incremental">增量导出（指定日期后的新链接）</el-radio>
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
            <el-option label="有效链接" value="valid" />
            <el-option label="无效链接" value="invalid" />
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
          <el-button type="primary" @click="handleExport" :loading="exporting">
            开始导出
          </el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 导出历史 -->
    <el-card class="mt-4" v-if="exportHistory.length > 0">
      <template #header>
        <span class="text-base font-semibold">导出历史</span>
      </template>

      <el-table :data="exportHistory" stripe>
        <el-table-column prop="website_name" label="网站" width="150" />
        <el-table-column prop="file_name" label="文件名" min-width="300" show-overflow-tooltip />
        <el-table-column prop="total_records" label="记录数" width="100" />
        <el-table-column prop="file_size" label="文件大小" width="120" />
        <el-table-column prop="export_time" label="导出时间" width="180" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleDownload(row.file_name)">
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
