# InputGate: development story

## The Problem

It started with something stupidly mundane: my mouse wouldn't scroll up.

Scrolling down worked every single time—smooth, responsive, completely normal. But rolling the wheel upward produced almost nothing. It would occasionally stutter or catch a single line, but for the most part, scrolling up was completely dead.

I use a Turtle Beach Kone II Air. If you search Reddit, iFixit, or manufacturer forums for "Kone scroll wheel issue," you find dozens of threads pointing to a single culprit: mechanical rotary encoder failure. Dust, lint, worn contacts, or grease. The community recommendations were familiar:
- Vigorously roll the mouse upside down against a mousepad for 15 seconds.
- Blast compressed air into the wheel gap.
- Disassemble the shell to clean or solder in a replacement encoder.

I was ready to accept it was a hardware failure and grab compressed air. But then I noticed my setup: the mouse was plugged into a USB-C cable charging from the PC, while its 2.4GHz wireless USB dongle was also plugged into the back of the motherboard.

On a whim, I pulled the USB cable out of the mouse, leaving only the wireless dongle connected. The scroll wheel immediately worked. Scrolling up was instant and smooth. Plug the cable back in to charge? Scroll-up broke again immediately.

This wasn't hardware failure at all. The rotary encoder was fine. The issue was entirely in the software layer.

Checking `/proc/bus/input/devices` showed what Linux was actually dealing with:

```text
I: Bus=0003 Vendor=10f5 Product=5007 Version=0110
N: Name="Turtle Beach Kone II Air Dongle Mouse"
H: Handlers=mouse0 event5 

I: Bus=0003 Vendor=10f5 Product=5005 Version=0110
N: Name="Turtle Beach Kone II Air Mouse"
H: Handlers=mouse1 event13
```

Linux didn't see one mouse connected through two interfaces. It saw **two completely separate mice**, each with its own Product ID (`5007` for the receiver, `5005` for the cable).

When moving the mouse or scrolling the wheel, both the dongle and the cable were firing HID reports into the kernel simultaneously. At the Linux input layer and the Wayland compositor, two streams of relative wheel deltas (`REL_WHEEL` and `REL_WHEEL_HI_RES`) were colliding. While negative deltas (scrolling down) managed to register, positive deltas (scrolling up) were conflicting, cancelling out, or being dropped as duplicate packets.

### The wider problem

Unplugging either connection fixes the conflict. But that means every time the battery gets low, you have to reach around your desk to unplug the dongle, charge via cable, and then plug the dongle back in when you're done—or rely on a dedicated socketed wall charger just to charge your mouse.

And this isn't unique to Turtle Beach. Modern gaming and productivity peripherals all ship with both a 2.4GHz dongle and a charging cable. When plugged in to charge, Linux treats them as two fighting devices by default, and there is no built-in arbitration mechanism to handle it.

## Expanding the scope

Once I understood what was actually happening with the mouse, I realized this probably isn't just a quirk of the Turtle Beach Kone, or even just mice in general. It pointed to a broader blind spot in how Linux manages input peripherals.

Many modern wireless keyboards operate on the exact same architecture: a 2.4GHz receiver permanently plugged into the back of the PC, and a USB-C cable for charging.

### The vision for InputGate

The project stopped being a one-off "dongle fix" and took on a much clearer identity: **InputGate**. 

Instead of treating input devices as static hardware nodes that the OS blindly reads at all times, InputGate would act as a gatekeeper:
- **Automatic arbitration**: Automatically silence the wireless receiver when a charging cable is attached (or treat the cable purely as a silent power source).
- **Exclusion policies**: Automatically disable the internal laptop keyboard whenever an external keyboard is detected.

## The architecture

With the problem defined, I had to choose how to actually build InputGate.

I wanted this to be a desktop application, but I also wanted an interface that felt modern and custom. I'm currently learning React, so the idea of building a web-based frontend paired with a Python backend was immediately appealing (I know Python quite well):
- **Frontend (`src/frontend/`)**: React running on Vite.
- **Backend (`src/inputgate/`)**: Python for communicating directly with the Linux input subsystem.

I chose a single `src/` layout holding both `src/frontend/` (React/Vite) and `src/inputgate/` (Python), configuring `pyproject.toml` to build the Python package while ignoring the frontend's `node_modules`.


## The input event struct

Before writing full application code, I needed to figure out how I was going to make this work. How will I scan for devices? How will I categorise them to specific peripherals (plus naming)? And how will I effectively mute them?

First, I got to looking into Linux hardware handling. I learned about device files, which live under `/dev/input/`. In Linux, hardware doesn't hide behind driver software like Windows. It sits on the filesystem as a character device: a live data pipe directly from the kernel, rather than a regular file sitting on an SSD. That explained why opening one in `nano` threw a red warning, and running `cat` dumped a live wall of scrambled binary characters.

The Linux kernel header `<linux/input.h>` exposes how it structures input events, and it helped a lot in visualising how I was going to eventually categorise peripherals:

```c 
struct input_event {
    struct timeval time; // timestamp (seconds & microseconds)
    __u16 type;          // event type (16-bit)
    __u16 code;          // event code (16-bit)
    __s32 value;         // event value (32-bit signed)
};
```

On 64-bit Linux, this struct is always exactly 24 bytes. So I had a starting point: build a parser that could directly read input events from devices.


## Device discovery and the grouping puzzle

So I started experimenting and getting Python to read 24-byte packets from `/dev/input/event5` was a good proof of concept, but now needed a way to dynamically discover what was plugged in.

Linux keeps a live text registry of all connected input devices at `/proc/bus/input/devices`. Reading it gives you everything as one block for each input device: the device name, the handler (`eventX`), the hardware Vendor and Product IDs, and the physical port path (`Phys=`).

I wrote a helper, `getFieldFromDeviceBlock()`, to parse those blocks. It handled quoted strings, key-value pairs, and space-separated lists cleanly.

Then the real puzzle showed up.

When I ran the scanner against my own machine, my Turtle Beach mouse didn't show up once. It showed up four times:
1. The mouse pointer (`event5`)
2. Consumer control (`event6`)
3. System control (`event7`)
4. The base macro device (`event4`)

Under the USB standard (HID), modern gaming mice aren't just pointers. They are multi-function composites. Media keys (volume up/down) are routed through consumer control. Sleep/wake buttons go through system control. And if you bind a side thumb button to a keyboard key, the mouse has to literally pretend to be a physical keyboard to type it.

That meant if I wanted to silence the mouse, I couldn't just mute one node; I had to mute all four nodes together.

### The filtering trap

My first instinct was to write a filter that kept only devices with names containing "mouse" or "keyboard".

That immediately broke. While one event may have had "Mouse" in the title, its sibling nodes were named things like `Turtle Beach Kone II Air Consumer Control`. A naive name filter threw three out of the four nodes in the bin before I even had a chance to group them. So I had to rely on something else.

The answer was in the `P: Phys=` line.

In the Linux kernel's input driver, every interface created by a USB device shares the same hardware bus address, with `/input0`, `/input1`, etc., appended to the end. My dongle's nodes all shared `usb-0000:10:00.0-2`, and the wired cable shared `usb-0000:10:00.0-5.4`. Those were the specific USB addresses respectively.

From there, the pipeline became clean:
1. Filter for input peripherals (any device matching a keyword like "mouse" or "keyboard").
2. Scoop up all sibling nodes sharing that exact physical port into an `InputDeviceGroup`.

Running it on my machine returned clean, deduplicated physical peripherals in milliseconds:

```text
Device Group: Turtle Beach Kone II Air Dongle
Device Group: Logitech Gaming Keyboard G213
```
