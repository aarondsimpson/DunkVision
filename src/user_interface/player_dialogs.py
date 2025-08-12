from tkinter import messagebox

def confirm_quit():
    return messagebox.askyesno("Quit", "Unsaved work will be lost. Quit?")