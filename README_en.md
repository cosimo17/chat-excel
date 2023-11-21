[中文](README.md)
# CHAT-EXCEL
Large language model make Excel simpler. Using a conversational AI model to assist in Excel data analysis and chart drawing.

# Demo
![demo1](assets/demo1.gif)

# Shortcut keys
+ Ctrl + Q, send your requirement to AI
+ Ctrl + A, collapse/expand the chat widget
+ Ctrl + Z, undo

# introduction
Use Pandas to read Excel data and represent the sheet as a DataFrame object.
Use AI to generate code for processing DataFrames, use a code interpreter to execute the code and feedback the results on the GUI, and use Matplotlib to draw charts.
It is still under development and may be unstable, and in some cases it may crash.
Part of the code for the interpreter is borrowed from[KillianLucas/open-interpreter](https://github.com/KillianLucas/open-interpreter/tree/main)    
Known issues：
+ In some cases, AI may provide incorrect code
+ Excel with merged cells is not supported
+ The header of Excel must be in the first row