import tkinter as tk
import main as ys

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.lights = dict()

    def create_widgets(self):
        self.lightList = tk.Listbox(self)
        ys.allEnabled = False
        ys.discover_lights()
        print("Found lights: ", ys.lights_available)
        for (name, light) in ys.lights_available.items():
          light.enabled = True
          self.lightList.insert(tk.END, name)
        self.lightList.selection_set(0,len(ys.lights_available) - 1)
        self.lightList.pack(side="top")

        self.quit = tk.Button(self, text="QUIT", fg="red",
                              command=self.master.destroy)
        self.quit.pack(side="bottom")

    def start_lighting(self):
        self.lightList.curselection()
        print("hi there, everyone!")
    def quit_all(self):
        self.master.destroy

root = tk.Tk()
app = Application(master=root)
app.mainloop()
