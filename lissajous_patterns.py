# -*- coding: utf-8 -*-
"""
lissajous patterns with compound sand pendulum
"""
from tkinter import Tk, Label, Button, LEFT, RIGHT, Entry, Checkbutton, IntVar, BooleanVar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np, matplotlib.pyplot as plt
from fractions import Fraction

plt.rc("font", size=15)

"""
Sand pendulum functions are defined here. These do the maths given the input
parameters. These are later used in the animation functions below.
"""

def lissajous_constants(x0,       # m
                        v_x0,     # m/s
                        y0,       # m
                        v_y0,     # m/s
                        l_x=1,   # m
                        l_y=.5,   # m
                        warnings=False,
                        debug=False):

    """ function to calculate the coefficients for a given set of sand
    pendulums. The coefficients are the amplitude, angular velocity, and phase
    shift for each of the two pendulums. """

    # constants
    g = 9.81  # m/s^2
    w_x = np.sqrt(g/l_x)  # (overall) angular velocity
    w_y = np.sqrt(g/l_y)
    T_x = 2*np.pi/w_x  # period
    T_y = 2*np.pi/w_y

    # calculate initial angle and angular velocity from init. pos. and vel.
    # p = angle; q = angular velocity; r = angular acceleration
    p_x0 = x0 / l_x
    p_y0 = y0 / l_y
    q_x0 = v_x0 / l_x
    q_y0 = v_y0 / l_y

    # calculate amplitude A and phase d
    A_x = np.sqrt(p_x0**2 + q_x0**2/w_x**2)
    A_y = np.sqrt(p_y0**2 + q_y0**2/w_y**2)
    d_x = np.arctan2(-q_x0, (p_x0*w_x))
    d_y = np.arctan2(-q_y0, (p_y0*w_y))

    if debug is True:
        print("period T_x =", T_x, "seconds")
        print("period T_y =", T_y, "seconds")
        print("angular velocity w_x =", w_x, "radians / second")
        print("angular velocity w_y =", w_y, "radians / second")

        print("initial position x0 =", x0, "metres")
        print("initial position y0 =", y0, "metres")
        print("initial velocity v_x0 =", v_x0, "metres / second")
        print("initial velocity v_y0 =", v_y0, "metres / second")

        print("initial angle p_x0 =", p_x0, "radians")
        print("initial angle p_y0 =", p_y0, "radians")
        print("initial angular velocity q_x0 =", q_x0, "radians / second")
        print("initial angular velocity q_y0 =", q_y0, "radians / second")

        print("phase shift d_x =", d_x, "radians")
        print("phase shift d_y =", d_y, "radians")
        print("amplitude A_x =", A_x, "radians")
        print("amplitude A_y =", A_y, "radians")

    if warnings is True:
        isochronism_limit = 0.1
        for amp, name in zip((A_x, A_y), ("A_x", "A_y")):
            if amp > isochronism_limit:
                print("Warning: {} is > {:0.3f} radians;".format(name, isochronism_limit),
                      "it is {:0.3f} radians ({:0.3f} degrees)".format(amp, np.degrees(amp)),
                      "\nThis breaks the isochronism limit.")

        upper_limit = np.radians(20)
        for amp, name in zip((A_x, A_y), ("A_x", "A_y")):
            if amp > upper_limit:
                print("Warning: {} is > {:0.3f} radians;".format(name, upper_limit),
                      "it is {:0.3f} radians ({:0.3f} degrees)".format(amp, np.degrees(amp)),
                      "\nThis breaks the upper limit for predictable pendulum behaviour.")

    return A_x, A_y, w_x, w_y, d_x, d_y


def lissajous_range(A_x, A_y, w_x, w_y, d_x, d_y, l_x, l_y, t_max=1,
                    d_time=.03):
    """ function to calculate the x, y trajectory of a sand pendulum given the
    coefficients, and a time range. """
    # calculate time-dependent variables
    t = np.arange(0, t_max, d_time)  # time vector
    p_x = A_x * np.cos(w_x*t + d_x)  # angle
    p_y = A_y * np.cos(w_y*t + d_y)
    xs = l_x * p_x
    ys = l_y * p_y
    return xs, ys


def lissajous_point(A_x, A_y, w_x, w_y, d_x, d_y, l_x, l_y, t):
    """ function to evaluate the position of a sand pendulum at a specific
    instant, given the coefficients and a time value. """
    # calculate time-dependent variables
    p_x = A_x * np.cos(w_x*t + d_x)  # angle
    p_y = A_y * np.cos(w_y*t + d_y)
    x = l_x * p_x
    y = l_y * p_y
    return x, y


# %% tkinter gui

class SandPendulumGUI:
    def __init__(self, window, l_x=1, l_y=.64, t_max=5, d_time=.03):
        self.window = window  # store handle to window
        window.title("Sand pendulum Lissajous patterns")

        # initialise pendulum parameters
        self.x0 = None
        self.y0 = None
        self.v_x0 = None
        self.v_y0 = None
        self.l_x = l_x
        self.l_y = l_y
        self.t_max = t_max
        self.d_time = d_time
        self.speed_multiplier = 4  # relating drag distance to initial velocity
        self.active = False
        self.predict_path = BooleanVar()
        self.predict_path.initialize(True)
        self.show_ratio = BooleanVar()
        self.show_ratio.initialize(False)

        # create the mpl Figure instance on which to plot
        fig = Figure(figsize=(5, 5))
        ax = fig.add_subplot(111)
        self.fig = fig  # store these handles
        self.ax = ax
        ax.set_aspect("equal")  # equal aspect ratio
        for spine in ax.spines.values():  # move spines to origin
            spine.set_position(("data", 0))
        lim = -1, 1  # set axes limits
        plt.setp(ax, xlim=lim, ylim=lim, xticks=lim, yticks=lim,)

        # define the canvas to house the mpl Figure
        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().pack()
        canvas.draw()
        # set the default mathtext font
        plt.rcParams['mathtext.fontset'] = 'stix'

        # define matplotlib handlers for mouse events
        canvas.mpl_connect('button_press_event', self.canvasClick)
        canvas.mpl_connect('button_release_event', self.canvasRelease)

        # define entry fields for parameters
        def makeEntry(parent, caption, default, side=None, width=None,
                      **options):
            Label(parent, text=caption).pack(side=side)
            entry = Entry(parent, **options)
            if width is not None:
                entry.config(width=width)
            entry.pack(side=side)
            entry.insert(0, default)
            return entry

        self.l_x_entry = makeEntry(window, "Total length: L (m)",
                                   self.l_x)
        self.l_y_entry = makeEntry(window, "Length of pendulum 2: l (m)",
                                   self.l_y)
        self.t_max_entry = makeEntry(window, "Time to simulate: t_max (s)",
                                     self.t_max)
        self.d_time_entry = makeEntry(window, "Time increment: d_time (s)",
                                      self.d_time)
        self.speed_multiplier_entry = makeEntry(window,
                                                "Throw speed multiplier (-)",
                                                self.speed_multiplier)

        # define checkbutton for predict path yes/no
        cb = Checkbutton(window, text="predict path", onvalue=True,
                         offvalue=False,
                         command=lambda: self.toggle(self.predict_path))
        cb.pack()
        if self.predict_path.get():
            cb.select()  # set to checked by default
        self.predict_path_button = cb

        # define checkbutton for displaying mathtext yes/no
        cb = Checkbutton(window, text="show ratio", onvalue=True,
                         offvalue=False,
                         command=lambda: self.toggle(self.show_ratio))
        cb.pack()
        if self.show_ratio.get():
            cb.select()  # set to checked by default
        self.show_ratio_button = cb

        # define clear canvas button
        self.clear_button = Button(window, text="Clear",
                                   command=self.clear_axes)
        self.clear_button.pack()#side=LEFT)

        # define save figure button
        self.save_button = Button(window, text="Save figure",
                                   command=self.save_figure)
        self.save_button.pack()#side=LEFT)

        # define exit button
        self.close_button = Button(window, text="Close", command=window.quit)
        self.close_button.pack()#side=RIGHT)

    def toggle(self, var):
        var.set(not var.get())

    def canvasClick(self, event):
        if event.button != 1:  # ignore mouse clicks that aren't button 1
            return None
        self.x0 = event.xdata
        self.y0 = event.ydata
        self.ax.plot(event.xdata, event.ydata, ".k")
        self.fig.canvas.draw_idle()

    def canvasRelease(self, event):
        self.update_params()  # update parameters from entry fields
        self.v_x0 = event.xdata-self.x0
        self.v_y0 = event.ydata-self.y0
        self.ax.plot(event.xdata, event.ydata, ".k")
        if (self.v_x0 != 0) or (self.v_y0 != 0):
            self.ax.arrow(self.x0, self.y0, self.v_x0, self.v_y0, zorder=10,
                          width=0.02, lw=0, color="firebrick",
                          length_includes_head=True)
        self.fig.canvas.draw_idle()
        self.v_x0 = self.speed_multiplier * self.v_x0
        self.v_y0 = self.speed_multiplier * self.v_y0
        # recalculate coefficients
        temp = lissajous_constants(self.x0, self.v_x0, self.y0, self.v_y0,
                                   self.l_x, self.l_y)

        if self.show_ratio.get() is True:
            ratio = Fraction(str(np.sqrt(self.l_y/self.l_x)))
            s = r"$\sqrt{{l\,/\,L}}=\frac{{{}}}{{{}}}={}$".format(ratio.numerator,
                        ratio.denominator, ratio.numerator/ratio.denominator)
            self.ax.text(-1, 1, s, ha="left", va="top", fontsize=20,
                         color=".5", zorder=999, alpha=1)

        # plot path
        self.plot_lissajous(*temp, self.l_x, self.l_y, self.t_max, self.d_time)

    def update_params(self):
        # update the parameters from the entry fields
        self.l_x = float(self.l_x_entry.get())
        self.l_y = float(self.l_y_entry.get())
        self.t_max = float(self.t_max_entry.get())
        self.d_time = float(self.d_time_entry.get())
        self.speed_multiplier = float(self.speed_multiplier_entry.get())

    def clear_axes(self):
        for artist in self.ax.lines + self.ax.collections + self.ax.artists + self.ax.texts:
            artist.remove()  # remove all artists (inverse Cass Art)
        self.fig.canvas.draw_idle()  # update the axes

    def save_figure(self):
        self.fig.savefig("output.png")

    def plot_lissajous(self, A_x, A_y, w_x, w_y, d_x, d_y, l_x, l_y, t_max,
                       d_time):
        self.active = True  # set the active flag so no other events are logged
        # generate the x, y data
        xs, ys = lissajous_range(A_x, A_y, w_x, w_y, d_x, d_y, l_x, l_y, t_max,
                                 d_time)

        colours = plt.cm.inferno_r(np.linspace(.1, 1, len(xs)))
        if self.predict_path.get() is True:
            # static plot
            for ii, c in zip(range(1, len(xs)), colours):
                self.ax.plot((xs[ii-1], xs[ii]), (ys[ii-1], ys[ii]), "-", c=c)

        # animated plot
        def update_plot():
            nonlocal ii, traj
            if ii > len(xs):
                return None  # exit the loop
            c = colours[:ii]
            traj.set_color(c)
            traj.set_offsets(np.vstack([xs[:ii], ys[:ii]]).T)
            self.fig.canvas.draw_idle()
            ii += 1
            self.window.after(int(d_time*1000), update_plot)

        traj = self.ax.scatter([], [], cmap=plt.cm.inferno_r)
        ii = 0
        update_plot()
        self.active = False  # reset the active flag to false when done


root = Tk()
gui = SandPendulumGUI(root, )
root.mainloop()
root.destroy()