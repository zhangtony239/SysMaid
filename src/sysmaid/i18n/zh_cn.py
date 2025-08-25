# src/sysmaid/i18n/zh_cn.py
translations = {
  "init.admin.error.title": "权限错误",
  "init.admin.error.message": "SysMaid 需要管理员权限才能正常运行。",
  "init.admin.skip.message": "已进入CI模式：UAC检查已被跳过。如果您是普通用户，请立即停止并检查您的环境变量。",
  "get_top_processes.result.header": "消耗CPU资源最多的 {count} 个进程：",
  "get_top_processes.result.item": "  - PID: {pid}, 名称: {name}, CPU: {cpu}%",
  "get_top_processes.result.item.error": "  - PID: {pid}, 名称: {name}, CPU: N/A (进程已退出)",
  "get_top_processes.return.general_error": "错误：无法获取进程信息。{error}",
  "alarm.title": "SysMaid 警报"
}