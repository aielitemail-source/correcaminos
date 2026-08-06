Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c omniroute start", 0, False
Set WshShell = Nothing
