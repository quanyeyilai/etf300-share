' 每日静默执行：更新数据 -> 抓取板块估值 -> 微信推送 -> 加密打包 -> 提交推送
' 供 Windows 计划任务调用，无窗口；日志在 data\notify.log
Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = "C:\Users\Administrator\Desktop\vibe\etf_share"
ws.Run "cmd /c ""daily.bat >> data\notify.log 2>&1""", 0, False
