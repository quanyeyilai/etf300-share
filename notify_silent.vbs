' 每日静默执行：抓取板块估值 + 推送到微信（供 Windows 计划任务调用，无窗口）
Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = "C:\Users\Administrator\Desktop\vibe\etf_share"
ws.Run "cmd /c ""python sector.py >> data\notify.log 2>&1 && python notify.py >> data\notify.log 2>&1""", 0, False
