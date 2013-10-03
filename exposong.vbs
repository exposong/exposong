
Set filesys = CreateObject("Scripting.FileSystemObject")
Set WshShell = WScript.CreateObject("WScript.Shell")

If filesys.FileExists("C:\Python26\pythonw.exe") Then
  WshShell.Run "\Python26\pythonw.exe bin\exposong"
ElseIf filesys.FileExists("C:\Python25\pythonw.exe") Then
  WshShell.Run "\Python25\pythonw.exe bin\exposong"
Else
  MsgBox("Could not find a Python installation.")
End If
