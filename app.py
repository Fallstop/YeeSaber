from tkinter import *
from tkinter.ttk import *
import main as ys
import threading

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.lights = dict()

    def create_widgets(self):
        # Create light list
        self.lightList = Listbox(self)
        ys.allEnabled = False
        ys.discover_lights()
        print("Found lights: ", ys.lights_available)
        for name in ys.lights_available.keys():
          ys.lights_enabled.add(name)
          self.lightList.insert(END, name)
        self.lightList.select_set(0,len(ys.lights_available) - 1)
        self.lightList.pack(side="top")

        # Buttons
        self.start = Button(self, text="Start", command=self.start_lighting)
        self.start.pack(side="bottom")
        self.quit = Button(self, text="Quit", command=self.quit_all)
        self.quit.pack(side="bottom")

    def start_lighting(self):
        selected_ids = self.lightList.curselection()
        enabledLights = [self.lightList.get(int(l)) for l in selected_ids]
        ys.lights_enabled = set(enabledLights)
        print("Starting lights...", ys.get_selected())
        ys.setUpLights()
        print("Done, opening web socket")
        self.client = threading.Thread(target=ys.start_socket)
        self.client.daemon = True
        self.client.start()
        print("Done.")

    def quit_all(self):
        print("Disconnecting lights...")
        ys.disconnectLights()
        print("Done. Disconnecting Beat Saber...")
        ys.wsApp.keep_running = False
        print("Done. Exiting...")
        self.master.destroy()

root = Tk()
app = Application(master=root)
app.mainloop()
