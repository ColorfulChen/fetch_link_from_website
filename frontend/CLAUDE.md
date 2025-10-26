# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

这是网页链接爬虫系统的前端项目，基于 pure-admin-thin 模板构建，使用 Vue 3 + TypeScript + Element Plus + TailwindCSS。

**技术栈**:
- Vue 3.5 + TypeScript
- Vite 7 (构建工具)
- Element Plus 2.10 (UI 组件库)
- TailwindCSS 4 (CSS 框架)
- Pinia 3 (状态管理)
- Vue Router 4 (路由管理)
- Axios (HTTP 客户端)

## 常用命令

```bash
# 安装依赖(必须使用 pnpm)
pnpm install

# 开发模式
pnpm dev

# 构建生产版本
pnpm build

# 构建后预览
pnpm preview:build

# 代码检查和格式化
pnpm lint              # 运行所有 lint
pnpm lint:eslint       # ESLint 检查
pnpm lint:prettier     # Prettier 格式化
pnpm lint:stylelint    # CSS/SCSS 样式检查

# 类型检查
pnpm typecheck

# 清理缓存
pnpm clean:cache
```

**注意**: 项目强制使用 pnpm 包管理器(在 package.json 中配置了 preinstall 钩子)。

## 核心架构

### 目录结构

```
src/
├── api/                # API 接口定义
├── assets/             # 静态资源(图片、字体、SVG)
├── components/         # 全局可复用组件
├── config/             # 配置文件
├── directives/         # Vue 自定义指令
├── layout/             # 布局组件
├── plugins/            # 插件配置
├── router/             # 路由配置
├── store/              # Pinia 状态管理
├── style/              # 全局样式
├── utils/              # 工具函数
├── views/              # 页面视图
├── App.vue             # 根组件
└── main.ts             # 应用入口
```

## 模块功能说明

### 1. 路由模块 (router/)

**核心文件**: `router/index.ts`

- **自动导入路由**: 使用 `import.meta.glob` 自动导入 `router/modules/` 下的所有路由模块
- **路由扁平化**: 将三级及以上路由转换为二级路由,优化性能
- **路由守卫**: 实现登录验证、权限控制、页面标题设置、KeepAlive 缓存管理
- **路由白名单**: `/login` 等无需登录即可访问的路由
- **动态路由**: 支持根据用户权限动态加载路由

**关键功能**:
- `resetRouter()`: 重置路由(用于登出)
- `beforeEach`: 全局前置守卫,处理登录状态、权限验证
- `afterEach`: 全局后置守卫,关闭进度条

### 2. 状态管理模块 (store/)

**使用 Pinia 进行状态管理**,包含以下子模块:

#### store/modules/user.ts
- 用户信息管理(头像、用户名、昵称)
- 用户角色和权限
- 登录/登出操作
- Token 刷新机制

#### store/modules/permission.ts
- 菜单管理(静态菜单 + 动态菜单)
- 路由权限过滤
- 页面缓存管理(KeepAlive)
- 缓存操作: refresh(刷新)、add(添加)、delete(删除)

#### store/modules/multiTags.ts
- 多标签页管理
- 标签页的增删改操作
- 标签页缓存

#### store/modules/app.ts
- 应用全局状态(侧边栏展开/折叠、设备类型)
- 响应式布局管理
- 视口尺寸监听

#### store/modules/settings.ts
- 布局设置(垂直/水平/混合布局)
- 主题设置
- 界面配置(固定头部、隐藏标签等)

#### store/modules/epTheme.ts
- Element Plus 主题色管理
- 动态主题切换

### 3. HTTP 请求模块 (utils/http/)

**核心文件**: `utils/http/index.ts`

- **请求/响应拦截器**:
  - 自动添加 Authorization 头
  - Token 过期自动刷新
  - 全局进度条(NProgress)
- **请求白名单**: `/login`, `/refresh-token` 等不需要 Token 的接口
- **错误处理**: 统一的错误拦截和处理
- **API 方法**: `http.get()`, `http.post()`, `http.request()`

**使用示例**:
```typescript
import { http } from "@/utils/http";
const result = await http.get<ResponseType>("/api/endpoint");
```

### 4. 布局系统 (layout/)

**主布局文件**: `layout/index.vue`

支持三种布局模式:
- **vertical**: 垂直布局(侧边栏在左侧)
- **horizontal**: 水平布局(菜单在顶部)
- **mix**: 混合布局(侧边栏 + 顶部菜单)

#### 布局组件说明:

**lay-sidebar/**: 侧边栏组件
- `NavVertical.vue`: 垂直导航菜单
- `NavHorizontal.vue`: 水平导航菜单
- `NavMix.vue`: 混合导航菜单
- `components/SidebarLogo.vue`: Logo 显示
- `components/SidebarItem.vue`: 菜单项递归渲染
- `components/SidebarBreadCrumb.vue`: 面包屑导航

**lay-navbar/**: 顶部导航栏
- 用户信息显示
- 全屏切换
- 消息通知
- 设置面板入口

**lay-tag/**: 标签页组件
- 多标签页显示
- 标签关闭/刷新/固定
- 右键菜单操作

**lay-content/**: 主内容区
- 路由视图渲染
- KeepAlive 缓存控制

**lay-search/**: 全局搜索
- 菜单搜索
- 搜索历史

**lay-notice/**: 消息通知
- 通知列表
- 消息提醒

**lay-setting/**: 系统设置面板
- 布局切换
- 主题配置
- 界面设置

**lay-panel/**: 折叠面板
- 侧边折叠面板

**lay-footer/**: 页脚组件

**lay-frame/**: iframe 框架
- 外部页面嵌入

#### 布局 Hooks (layout/hooks/):

- `useLayout.ts`: 布局配置管理
- `useNav.ts`: 导航相关逻辑
- `useTag.ts`: 标签页操作
- `useDataThemeChange.ts`: 主题切换
- `useMultiFrame.ts`: 多 iframe 管理
- `useBoolean.ts`: 布尔状态管理

**响应式布局**:
- 0-760px: 移动端,隐藏侧边栏
- 760-990px: 平板,折叠侧边栏
- 990px+: 桌面,展开侧边栏

### 5. 全局组件 (components/)

#### ReIcon/
- 图标组件封装
- 支持 Iconify 在线/离线图标
- 支持 Iconfont 图标库
- `IconifyIconOnline`: 在线图标
- `IconifyIconOffline`: 离线图标
- `FontIcon`: 字体图标

#### ReDialog/
- 对话框组件封装
- 基于 Element Plus Dialog 增强

#### RePureTableBar/
- 表格工具栏
- 表格列配置
- 打印功能

#### ReAuth/
- 按钮级权限控制组件
- 根据用户权限显示/隐藏元素

#### RePerms/
- 页面级权限控制组件
- 权限验证

#### ReSegmented/
- 分段控制器组件

#### ReText/
- 文本组件封装

#### ReCol/
- 栅格列组件

### 6. 自定义指令 (directives/)

所有指令在 `main.ts` 中自动注册为全局指令。

#### v-auth
- 权限指令
- 根据用户权限控制元素显示
- 用法: `v-auth="'system:user:add'"`

#### v-perms
- 权限指令(另一种实现)
- 支持多权限验证
- 用法: `v-perms="['admin', 'editor']"`

#### v-copy
- 复制指令
- 点击元素复制内容到剪贴板
- 用法: `v-copy="textToCopy"`

#### v-longpress
- 长按指令
- 长按触发事件
- 用法: `v-longpress="handleLongPress"`

#### v-ripple
- 波纹效果指令
- 点击时显示 Material Design 波纹效果
- 用法: `v-ripple`

#### v-optimize
- 性能优化指令
- 图片懒加载等优化

### 7. 工具函数 (utils/)

#### utils/auth.ts
- Token 管理(获取、设置、删除)
- 用户信息本地存储
- 多标签页 Token 共享

#### utils/message.ts
- 消息提示封装
- 基于 Element Plus Message

#### utils/tree.ts
- 树形数据处理
- 构建层级树结构
- `buildHierarchyTree()`: 将扁平数组转为树形结构

#### utils/responsive.ts
- 响应式存储
- 窗口尺寸监听

#### utils/progress/
- 页面加载进度条
- NProgress 配置

#### utils/localforage/
- IndexedDB 本地存储封装
- 大数据量存储方案

#### utils/mitt.ts
- 事件总线
- 跨组件通信

#### utils/print.ts
- 打印功能
- 页面/表格打印

#### utils/sso.ts
- 单点登录相关

#### utils/propTypes.ts
- Vue Props 类型验证工具

#### utils/globalPolyfills.ts
- 全局 Polyfills
- 兼容性处理

#### utils/preventDefault.ts
- 事件阻止默认行为

### 8. 插件配置 (plugins/)

#### elementPlus.ts
- Element Plus 全局配置
- 组件默认属性设置
- 国际化配置

#### echarts.ts
- ECharts 图表库配置
- 按需引入图表组件

### 9. 配置文件 (config/)

#### config/index.ts
- 平台配置加载
- 从 `public/platform-config.json` 读取配置
- 全局配置注入
- 响应式存储命名空间

### 10. 页面视图 (views/)

#### views/login/
- 登录页面
- 包含登录表单、验证规则、动画效果
- `utils/rule.ts`: 表单验证规则
- `utils/motion.ts`: 动画配置
- `utils/static.ts`: 静态数据

#### views/welcome/
- 欢迎页/首页

#### views/error/
- 错误页面
- `403.vue`: 无权限页面
- `404.vue`: 页面不存在
- `500.vue`: 服务器错误

#### views/permission/
- 权限示例页面
- `button/`: 按钮级权限示例
- `page/`: 页面级权限示例

### 11. API 接口 (api/)

#### api/user.ts
- 用户相关 API
- 登录接口
- Token 刷新接口

#### api/routes.ts
- 动态路由 API
- 获取用户路由权限

## 重要注意事项

1. **包管理器**: 必须使用 pnpm,不要使用 npm 或 yarn

2. **路由模块**: 新增路由模块放在 `router/modules/` 下,会自动导入,文件名不要用 `remaining.ts`

3. **权限控制**:
   - 页面级权限在路由 meta 中配置 `roles: ['admin']`
   - 按钮级权限使用 `v-auth` 指令或 `<Auth>` 组件

4. **样式导入顺序**:
   - reset.scss (重置样式)
   - index.scss (全局样式)
   - tailwind.css (TailwindCSS)
   - element-plus/dist/index.css

5. **图标使用**:
   - 在线图标: `<IconifyIconOnline icon="ep:warning" />`
   - 离线图标: `<IconifyIconOffline icon="info-filled" />`
   - 字体图标: `<FontIcon icon="iconfont-name" />`

6. **状态管理**: 使用 Pinia,不要使用 Vuex

7. **HTTP 请求**: 统一使用 `utils/http/index.ts` 中的 http 实例

8. **本地存储**:
   - 小数据: 使用 `storageLocal()` (基于 localStorage)
   - 大数据: 使用 `localforage` (基于 IndexedDB)

9. **主题配置**:
   - 配置文件: `public/platform-config.json`
   - 主题色切换: `store/modules/epTheme.ts`

10. **构建产物**: 构建后的文件在 `dist/` 目录,需要复制到后端的 `web/` 目录

11. **环境变量**:
    - 使用 `.env` 文件配置
    - 访问方式: `import.meta.env.VITE_*`

12. **TypeScript**: 项目使用严格的 TypeScript,确保类型安全

13. **代码规范**: 提交前运行 `pnpm lint` 确保代码符合规范

14. **响应式设计**: 使用 TailwindCSS 工具类 + SCSS 混合开发

15. **组件命名**:
    - 全局组件: 使用 `Re` 前缀(如 `ReIcon`, `ReDialog`)
    - 布局组件: 使用 `Lay` 前缀(如 `LayNavbar`, `LaySidebar`)
