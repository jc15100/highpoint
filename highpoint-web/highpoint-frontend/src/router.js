import { createWebHistory, createRouter } from "vue-router";

import Videos from "./apps/videos.vue";

const routes = [
    {
        path: '/video',
        component: Videos
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes: routes,
});

export default router;
