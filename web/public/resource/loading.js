/**
 * 初始化加载效果的svg格式logo
 * @param {string} id - 元素id
 */
 function initSvgLogo(id) {
  const svgStr = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" fill="none" width="120" height="120">
  <path d="M60 160 C60 160, 55 120, 65 95 C72 78, 78 68, 82 55 C85 46, 92 35, 100 30 C108 25, 118 28, 120 35 C122 42, 118 48, 115 52 L118 50 C122 46, 130 42, 135 45 C140 48, 138 55, 135 60 C132 65, 125 72, 120 78 C115 84, 112 92, 110 100 C108 108, 108 118, 110 128 C112 138, 118 148, 125 155 L140 160"
    stroke="currentColor" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M82 55 C78 60, 72 68, 68 78" stroke="currentColor" stroke-width="6" stroke-linecap="round" fill="none" opacity="0.7"/>
  <path d="M90 42 C85 50, 78 60, 72 72" stroke="currentColor" stroke-width="5" stroke-linecap="round" fill="none" opacity="0.5"/>
  <circle cx="108" cy="52" r="4" fill="currentColor"/>
  <line x1="40" y1="100" x2="55" y2="100" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.4"/>
  <line x1="35" y1="115" x2="55" y2="115" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.3"/>
  <line x1="42" y1="130" x2="58" y2="130" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.2"/>
  <line x1="50" y1="170" x2="150" y2="170" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.3"/>
</svg>`
  const appEl = document.querySelector(id)
  const div = document.createElement('div')
  div.innerHTML = svgStr
  if (appEl) {
    appEl.appendChild(div)
  }
}

function addThemeColorCssVars() {
  const key = '__THEME_COLOR__'
  const defaultColor = '#2d8cf0'
  const themeColor = window.localStorage.getItem(key) || defaultColor
  const cssVars = `--primary-color: ${themeColor}`
  document.documentElement.style.cssText = cssVars
}

addThemeColorCssVars()

initSvgLogo('#loadingLogo')
