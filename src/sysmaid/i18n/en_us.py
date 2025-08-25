# src/sysmaid/i18n/en_us.py
translations = {
  "init.admin.error.title": "Permission Error",
  "init.admin.error.message": "SysMaid requires administrator privileges to run properly.",
  "init.admin.skip.message": "CI mode activated: UAC check is bypassed. If you are a regular user, please stop and check your environment variables.",
  "get_top_processes.result.header": "Top {count} CPU-consuming processes:",
  "get_top_processes.result.item": "  - PID: {pid}, Name: {name}, CPU: {cpu}%",
  "get_top_processes.result.item.error": "  - PID: {pid}, Name: {name}, CPU: N/A (process has exited)",
  "get_top_processes.return.general_error": "Error: Could not retrieve top processes. {error}",
  "alarm.title": "SysMaid Alarm"
}