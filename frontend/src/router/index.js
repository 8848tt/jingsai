import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import MainLayout from '../layouts/MainLayout.vue'

function homePath(role) {
  if (role === 'admin') return '/admin/competitions'
  if (role === 'expert') return '/expert/competitions'
  return '/student/competitions'
}

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        beforeEnter(to, from, next) {
          const auth = useAuthStore()
          if (!auth.user) return next({ name: 'login' })
          next({ path: homePath(auth.user.role), replace: true })
        },
        component: { template: '<div />' },
      },
      {
        path: 'student/competitions',
        name: 'student-competitions',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentCompetitions.vue'),
      },
      {
        path: 'student/registrations',
        name: 'student-registrations',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentRegistrations.vue'),
      },
      {
        path: 'student/submissions',
        name: 'student-submissions',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentSubmissions.vue'),
      },
      {
        path: 'student/teams',
        name: 'student-teams',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentTeams.vue'),
      },
      {
        path: 'student/teams/:id',
        name: 'student-team-detail',
        meta: { roles: ['student'] },
        component: () => import('../views/student/TeamDetail.vue'),
      },
      {
        path: 'student/announcements/:id(\\d+)',
        name: 'student-announcement-detail',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentAnnouncementDetail.vue'),
      },
      {
        path: 'student/announcements',
        name: 'student-announcements',
        meta: { roles: ['student'] },
        component: () => import('../views/student/StudentAnnouncements.vue'),
      },
      {
        path: 'expert/competitions',
        name: 'expert-competitions',
        meta: { roles: ['expert'] },
        component: () => import('../views/expert/ExpertCompetitions.vue'),
      },
      {
        path: 'expert/competitions/:id/submissions',
        name: 'expert-submissions',
        meta: { roles: ['expert'] },
        component: () => import('../views/expert/ExpertSubmissions.vue'),
      },
      {
        path: 'admin/competitions',
        name: 'admin-competitions',
        meta: { roles: ['admin'] },
        component: () => import('../views/admin/AdminCompetitions.vue'),
      },
      {
        path: 'admin/registrations',
        name: 'admin-registrations',
        meta: { roles: ['admin'] },
        component: () => import('../views/admin/AdminRegistrations.vue'),
      },
      {
        path: 'admin/announcements/:id(\\d+)',
        name: 'admin-announcement-detail',
        meta: { roles: ['admin'] },
        component: () => import('../views/admin/AdminAnnouncementDetail.vue'),
      },
      {
        path: 'admin/announcements',
        name: 'admin-announcements',
        meta: { roles: ['admin'] },
        component: () => import('../views/admin/AdminAnnouncements.vue'),
      },
      {
        path: 'admin/submissions',
        name: 'admin-submissions',
        meta: { roles: ['admin'] },
        component: () => import('../views/admin/AdminSubmissions.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.user && (to.name === 'login' || to.name === 'register')) {
      return next({ path: homePath(auth.user.role), replace: true })
    }
    return next()
  }
  if (!auth.user) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }
  if (to.meta.roles && !to.meta.roles.includes(auth.user.role)) {
    return next({ path: homePath(auth.user.role), replace: true })
  }
  next()
})

export default router
