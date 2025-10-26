const Layout = () => import("@/layout/index.vue");

export default {
  path: "/crawler",
  name: "Crawler",
  component: Layout,
  redirect: "/crawler/websites",
  meta: {
    icon: "ep:operation",
    title: "爬虫管理",
    rank: 1
  },
  children: [
    {
      path: "/crawler/websites",
      name: "WebsiteManage",
      component: () => import("@/views/crawler/website/index.vue"),
      meta: {
        title: "网站管理",
        showLink: true
      }
    },
    {
      path: "/crawler/tasks",
      name: "TaskManage",
      component: () => import("@/views/crawler/task/index.vue"),
      meta: {
        title: "任务管理",
        showLink: true
      }
    },
    {
      path: "/crawler/tasks/:id",
      name: "TaskDetail",
      component: () => import("@/views/crawler/task/detail.vue"),
      meta: {
        title: "任务详情",
        showLink: false
      }
    },
    {
      path: "/crawler/schedules",
      name: "ScheduleManage",
      component: () => import("@/views/crawler/schedule/index.vue"),
      meta: {
        title: "调度管理",
        showLink: true
      }
    },
    {
      path: "/crawler/export",
      name: "DataExport",
      component: () => import("@/views/crawler/export/index.vue"),
      meta: {
        title: "数据导出",
        showLink: true
      }
    },
    {
      path: "/crawler/statistics",
      name: "Statistics",
      component: () => import("@/views/crawler/statistics/index.vue"),
      meta: {
        title: "统计监控",
        showLink: true
      }
    }
  ]
} satisfies RouteConfigsTable;
