import { computed, ref } from "vue";

export default function userRole() {
    const role = ref(sessionStorage.getItem('role') || '');

    return {
        role,
        isAdmin: computed(() => role.value === '管理员'),
        isTeacher: computed(() => role.value === '教师'),
        isStudent: computed(() => role.value === '学生')
    }
}