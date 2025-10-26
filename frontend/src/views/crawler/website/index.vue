<script setup lang="ts">
import { ref, onMounted, reactive } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  getWebsites,
  createWebsite,
  updateWebsite,
  deleteWebsite,
  type Website,
  type CreateWebsiteParams,
  type UpdateWebsiteParams
} from "@/api/websites";

defineOptions({
  name: "WebsiteManage"
});

// 表格数据
const loading = ref(false);
const tableData = ref<Website[]>([]);
const total = ref(0);

// 查询参数
const queryForm = reactive({
  status: "",
  page: 1,
  page_size: 20
});

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref("添加网站");
const formRef = ref();
const form = reactive<CreateWebsiteParams & { id?: string }>({
  name: "",
  url: "",
  crawl_depth: 3,
  max_links: 1000
});

// 表单验证规则
const rules = {
  name: [{ required: true, message: "请输入网站名称", trigger: "blur" }],
  url: [
    { required: true, message: "请输入网站URL", trigger: "blur" },
    { type: "url", message: "请输入有效的URL", trigger: "blur" }
  ],
  crawl_depth: [{ required: true, message: "请输入爬取深度", trigger: "blur" }],
  max_links: [{ required: true, message: "请输入最大链接数", trigger: "blur" }]
};

// 加载网站列表
const loadWebsites = async () => {
  loading.value = true;
  try {
    const res = await getWebsites(queryForm);
    if (res.success) {
      tableData.value = res.data;
      total.value = res.pagination.total;
    }
  } finally {
    loading.value = false;
  }
};

// 打开添加对话框
const handleAdd = () => {
  dialogTitle.value = "添加网站";
  Object.assign(form, {
    name: "",
    url: "",
    crawl_depth: 3,
    max_links: 1000
  });
  delete form.id;
  dialogVisible.value = true;
};

// 打开编辑对话框
const handleEdit = (row: Website) => {
  dialogTitle.value = "编辑网站";
  Object.assign(form, {
    id: row.id,
    name: row.name,
    url: row.url,
    crawl_depth: row.crawl_depth,
    max_links: row.max_links
  });
  dialogVisible.value = true;
};

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid: boolean) => {
    if (!valid) return;

    try {
      if (form.id) {
        // 编辑
        const { id, ...data } = form;
        await updateWebsite(id, data as UpdateWebsiteParams);
        ElMessage.success("更新成功");
      } else {
        // 添加
        await createWebsite(form);
        ElMessage.success("添加成功");
      }
      dialogVisible.value = false;
      loadWebsites();
    } catch (error) {
      // HTTP 拦截器已经显示了错误信息
    }
  });
};

// 切换状态
const handleToggleStatus = async (row: Website) => {
  try {
    const newStatus = row.status === "active" ? "inactive" : "active";
    await updateWebsite(row.id, { status: newStatus });
    ElMessage.success("状态更新成功");
    loadWebsites();
  } catch (error) {
    // HTTP 拦截器已经显示了错误信息
  }
};

// 删除网站
const handleDelete = (row: Website) => {
  ElMessageBox.confirm(`确定要删除网站"${row.name}"吗？`, "提示", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning"
  })
    .then(async () => {
      try {
        await deleteWebsite(row.id);
        ElMessage.success("删除成功");
        loadWebsites();
      } catch (error) {
        // HTTP 拦截器已经显示了错误信息
      }
    })
    .catch(() => {});
};

// 分页改变
const handlePageChange = (page: number) => {
  queryForm.page = page;
  loadWebsites();
};

// 查询
const handleQuery = () => {
  queryForm.page = 1;
  loadWebsites();
};

// 重置
const handleReset = () => {
  queryForm.status = "";
  queryForm.page = 1;
  loadWebsites();
};

onMounted(() => {
  loadWebsites();
});
</script>

<template>
  <div class="website-manage">
    <!-- 查询表单 -->
    <el-card class="mb-4">
      <div class="flex flex-wrap items-center gap-4">
        <div class="flex items-center gap-2">
          <span class="text-sm whitespace-nowrap">状态</span>
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            style="width: 150px"
            clearable
          >
            <el-option label="激活" value="active" />
            <el-option label="停用" value="inactive" />
          </el-select>
        </div>
        <div class="flex items-center gap-2">
          <el-button type="primary" @click="handleQuery">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleAdd">添加网站</el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card>
      <el-table v-loading="loading" :data="tableData" stripe>
        <el-table-column prop="name" label="网站名称" min-width="120" />
        <el-table-column
          prop="url"
          label="URL"
          min-width="200"
          show-overflow-tooltip
        />
        <el-table-column prop="domain" label="域名" min-width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === "active" ? "激活" : "停用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="crawl_depth" label="爬取深度" width="100" />
        <el-table-column prop="max_links" label="最大链接数" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button
              :type="row.status === 'active' ? 'warning' : 'success'"
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === "active" ? "停用" : "激活" }}
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
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

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="网站名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入网站名称" />
        </el-form-item>
        <el-form-item label="网站URL" prop="url">
          <el-input
            v-model="form.url"
            placeholder="请输入完整URL（包含 http:// 或 https://）"
          />
        </el-form-item>
        <el-form-item label="爬取深度" prop="crawl_depth">
          <el-input-number
            v-model="form.crawl_depth"
            :min="1"
            :max="10"
            controls-position="right"
          />
        </el-form-item>
        <el-form-item label="最大链接数" prop="max_links">
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
.website-manage {
  padding: 20px;
}
</style>
