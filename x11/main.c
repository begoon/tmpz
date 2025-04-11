#include <X11/Xlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MWM_HINTS_DECORATIONS (1L << 1)

int main()
{
    Display *display;
    Window window;
    int screen;
    GC gc;
    XEvent event;
    unsigned int win_width = 400, win_height = 200;
    int button_x = 150, button_y = 80, button_w = 100, button_h = 40;

    int drawing = 0;
    int last_x = 0, last_y = 0;
    int done = 0;

    display = XOpenDisplay(NULL);
    if (display == NULL)
    {
        fprintf(stderr, "unable to open X display\n");
        exit(1);
    }

    screen = DefaultScreen(display);

    XSetWindowAttributes attrs = {.background_pixel = WhitePixel(display, screen),
                                  .border_pixel = BlackPixel(display, screen),
                                  .override_redirect = True};

    window = XCreateWindow(display, RootWindow(display, screen),
                           100, 100, win_width, win_height,
                           10,
                           CopyFromParent,
                           InputOutput,
                           CopyFromParent,
                           CWBackPixel | CWBorderPixel,
                           &attrs);

    typedef struct
    {
        unsigned long flags;
        unsigned long functions;
        unsigned long decorations;
        long input_mode;
        unsigned long status;
    } MotifWmHints;

    MotifWmHints hints = {.flags = MWM_HINTS_DECORATIONS, .decorations = 0};
    Atom property = XInternAtom(display, "_MOTIF_WM_HINTS", False);

    XChangeProperty(display, window, property, property, 32, PropModeReplace, (unsigned char *)&hints, 5);

    XSelectInput(display, window, ExposureMask | ButtonPressMask | ButtonReleaseMask | PointerMotionMask);

    gc = XCreateGC(display, window, 0, NULL);
    XSetForeground(display, gc, BlackPixel(display, screen));

    XMapWindow(display, window);

    done = 0;
    while (!done)
    {
        XNextEvent(display, &event);

        switch (event.type)
        {
        case Expose:
            XDrawRectangle(display, window, gc, button_x, button_y, button_w, button_h);
            XDrawString(display, window, gc, button_x + 30, button_y + 25, "Exit", 4);
            break;

        case ButtonPress:
            if (event.xbutton.button == Button1)
            {
                int x = event.xbutton.x;
                int y = event.xbutton.y;

                if (x >= button_x && x <= button_x + button_w && y >= button_y && y <= button_y + button_h)
                {
                    done = 1;
                    break;
                }
                drawing = 1;
                last_x = x;
                last_y = y;
            }
            break;

        case ButtonRelease:
            if (event.xbutton.button == Button1)
                drawing = 0;
            break;

        case MotionNotify:
            if (drawing)
            {
                int x = event.xmotion.x;
                int y = event.xmotion.y;
                XDrawLine(display, window, gc, last_x, last_y, x, y);
                last_x = x;
                last_y = y;
            }
            break;
        }
    }

    XFreeGC(display, gc);
    XDestroyWindow(display, window);
    XCloseDisplay(display);
    return 0;
}
