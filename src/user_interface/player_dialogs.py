from tkinter import messagebox

MESSAGES = {
    "quit": {
        "title": "Quit", 
        "message": "Unsaved work will be lost. Quit?"
    },
}
#Will add more as they appear
#Will add "load" section for load-related messages
#Will add "save" section for save-related messages 


#For Yes/No confirmations based on a key from the messages dictionary
def confirm_action(key: str) -> bool: 
    message = MESSAGES[key]
    return messagebox.askyesno(message["title"], message["message"])

#Informational dialog that passes a custom title and a message, or a known key and 'none'
def information(key_or_title: str, message: str | None = None):
    if message is None:
        message = MESSAGES[key_or_title]
        return messagebox.showinfo(message["title"], message["message"])
    return messagebox.showinfo(key_or_title, message)

#Error dialog that passes the error title and message
def error(title: str, message: str):
    return messagebox.showerror(title, message)