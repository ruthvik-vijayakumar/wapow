import { ref, computed, watch } from 'vue'

export type Theme = 'light' | 'dark'

const theme = ref<Theme>((localStorage.getItem('wapow-theme') as Theme) || 'dark')

function applyTheme(t: Theme) {
  const root = document.documentElement
  if (t === 'dark') {
    root.classList.add('dark')
    root.classList.remove('light')
  } else {
    root.classList.add('light')
    root.classList.remove('dark')
  }
}

applyTheme(theme.value)

watch(theme, (newTheme) => {
  localStorage.setItem('wapow-theme', newTheme)
  applyTheme(newTheme)
})

export function useTheme() {
  const isDark = computed(() => theme.value === 'dark')

  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
  }

  const setTheme = (t: Theme) => {
    theme.value = t
  }

  return {
    theme,
    isDark,
    toggleTheme,
    setTheme,
  }
}
