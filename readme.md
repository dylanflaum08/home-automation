# Home Automation — Gesture-Controlled Smart Home

A Python-based home automation system that uses a camera and computer vision to control smart lights with hand gestures.

The project currently runs as a prototype on a Windows PC using a webcam. The long-term goal is to move the system onto a Raspberry Pi 5 with a dedicated camera so it can operate as a standalone always-on home automation device.

The system currently controls two Kasa smart plugs:

- **Desk Lamp** — physically located to the user's left
- **Cabinet Lamp** — physically located to the user's right

The ultimate goal is to combine **computer vision + smart-home control + voice commands** into a single local automation system.

---

## Project Goals

The project is being built incrementally.

### Current Goal

Use hand gestures detected through a camera to control two smart lamps.

### Long-Term Goal

Build a standalone Raspberry Pi home automation system that can:

- Recognize hand gestures
- Control multiple smart devices
- Work in low-light/night conditions
- Accept voice commands
- Run continuously without a PC
- Add additional automation features over time
- Potentially combine multiple input methods (gesture + voice)
- Eventually become a more general-purpose smart-home controller

---

# Current Architecture

The current system roughly follows:

```text
                    Webcam
                       |
                       v
              +----------------+
              |  OpenCV Camera |
              +----------------+
                       |
                       v
              +----------------+
              |    MediaPipe   |
              | Hand Landmarker|
              +----------------+
                       |
                       v
              +----------------+
              | Gesture Logic  |
              +----------------+
                       |
                       v
              +----------------+
              | Automation     |
              | Logic          |
              +----------------+
                       |
                       v
              +----------------+
              |  python-kasa   |
              +----------------+
                    /     \
                   /       \
                  v         v
          Desk Lamp     Cabinet Lamp
          Kasa Plug     Kasa Plug

Eventually this should become:

                  Raspberry Pi 5
                       |
                 Pi Camera
                       |
                       v
              Computer Vision
                       |
            +----------+----------+
            |                     |
       Hand Gestures          Voice Input
            |                     |
            +----------+----------+
                       |
                       v
               Automation Logic
                       |
                       v
                  python-kasa
                       |
              +--------+--------+
              |                 |
              v                 v
          Desk Lamp        Cabinet Lamp
Current Hardware
Raspberry Pi 5

Purchased/selected:

Raspberry Pi 5
2 GB RAM

The 2 GB model is being used because this project primarily needs:

Python
OpenCV
MediaPipe
Camera processing
Kasa networking
Future voice processing

The Pi 5 provides significantly more CPU performance than older Raspberry Pi models and should be much better suited to real-time computer vision.

Raspberry Pi Power Supply

CanaKit USB-C power supply:

5V / 5A
Designed for Raspberry Pi 5
27W-class power supply

The Pi 5 should be powered using the appropriate high-current USB-C supply.

Raspberry Pi Case

CanaKit Turbine Case.

The project also includes active cooling.

Raspberry Pi Cooling

CanaKit Mega Heat Sink + Fan.

This is important because the Raspberry Pi will be performing continuous computer-vision processing.

The system should monitor temperatures once it is running continuously.

Storage

SanDisk Ultra:

64 GB
microSD
A1
U1
V10
Class 10

64 GB should be more than sufficient for the operating system, Python environment, project files, models, logs, and normal development.

Camera
Arducam IMX290 STARVIS

The selected camera is an Arducam Raspberry Pi-compatible IMX290 STARVIS camera.

Important characteristics:

1080p
STARVIS low-light sensor
Approximately 102° wide angle
Automatic day/night switching
IR-cut filter
MIPI CSI connection
Raspberry Pi/libcamera compatible
Includes the required 15-pin → 22-pin cable
Fixed/manual focus
Why this camera?

One of the future requirements is for the system to work at night.

The IMX290's low-light performance and day/night switching should make it much more useful than a normal inexpensive webcam.

Important:

The camera does not automatically provide infrared illumination.

The sensor can perform well in low light and can switch its IR-cut filter, but if the room becomes completely dark, an external IR illuminator may eventually be needed.

That can be added later if necessary.

Smart Devices

The project currently uses two TP-Link Kasa smart plugs.

Desk Lamp

Kasa EP10P2.

Purpose:

Desk Lamp = user's left side

Known device information:

MAC: 20:E1:5D:EE:59:51
Current IP during development: 192.168.4.21

The IP address should not necessarily be assumed to remain permanent. Ideally the router should eventually reserve a DHCP address for the plug.

Cabinet Lamp

Kasa EP10P2.

Purpose:

Cabinet Lamp = user's right side

Known MAC:

20:E1:5D:EE:38:FA

The IP address has changed/discovery has been less consistent than the desk plug.

Eventually configure a DHCP reservation if possible.

Network

Current development network:

Wi-Fi SSID: Bigdog

Gateway:
192.168.4.1

PC:
192.168.4.30

Subnet:
255.255.252.0

CIDR:
192.168.4.0/22

Broadcast:
192.168.7.255

The Raspberry Pi will eventually connect to the same Wi-Fi network as the Kasa devices.

Software Stack
Python

Python 3.12.x

Development has been done on Windows.

OpenCV

Used for:

Camera access
Video frames
Image processing
Display/debugging
MediaPipe

The project uses Google's MediaPipe hand-tracking technology.

Important:

The installed MediaPipe version is approximately:

MediaPipe 0.10.35

Recent versions do not expose the older:

mp.solutions.hands

API in the same way older tutorials do.

The project therefore uses the newer MediaPipe Tasks / Hand Landmarker approach.

Hand Landmarker Model

The repository contains:

hand_landmarker.task

This model is required for the hand-tracking system.

Do not delete it.

python-kasa

The project uses:

python-kasa

for communicating with the Kasa smart plugs.

Current version used during development:

python-kasa 0.10.2
Important Kasa Authentication Issue

This is an important piece of project history.

The Kasa plugs use a newer authentication protocol/firmware configuration.

Normal python-kasa discovery/authentication can produce an error similar to:

AuthenticationError:
Device response did not match our challenge

The working implementation uses the newer KLAP transport/authentication approach, including:

KlapTransportV2

and:

IotProtocol

Do not automatically replace the existing Kasa connection code with a generic Device.connect() implementation without testing.

The project previously successfully controlled the Kasa plug using the KLAP v2 approach.

Environment Variables

Kasa credentials are stored in a .env file.

Example:

KASA_USERNAME=your_kasa_username
KASA_PASSWORD=your_kasa_password

The actual .env file must NEVER be committed to GitHub.

The repository should contain a .gitignore with at least:

.env
__pycache__/
*.pyc
.venv/
venv/

If credentials are ever accidentally committed to GitHub:

Stop pushing commits.
Remove the credentials from Git history.
Rotate/change the affected password or credentials.
Do not simply assume deleting the file from the latest commit is sufficient.
Current Gesture System

The system is designed so that physical left/right hand identity does not determine the command.

Either physical hand can perform the pointing gesture.

The other hand provides the command modifier.

1. Point + Open Hand = ON

Example:

Left hand:  Open palm
Right hand: Pointing left

Result:

Desk Lamp ON

Or:

Right hand: Open palm
Left hand: Pointing right

Result:

Cabinet Lamp ON

The important concept is:

OPEN HAND + POINT

The direction of the pointing finger determines which lamp is controlled.

2. Point + Fist = OFF

Example:

One hand: Fist
Other hand: Pointing toward lamp

Result:

Pointed-to lamp OFF

Again, the physical hand performing the point does not matter.

The system should interpret the roles:

Pointing hand
+
Modifier hand

rather than relying on:

Left physical hand
Right physical hand
3. Prayer Hands = Both Lamps ON

When both hands are together in a prayer-like position:

🙏

Result:

Desk Lamp ON
Cabinet Lamp ON

This is a global command.

4. Hang Loose / Shaka = Both Lamps OFF

A hang-loose gesture:

🤙

from either hand should turn both lamps off.

Result:

Desk Lamp OFF
Cabinet Lamp OFF

This gesture has previously caused false positives, particularly when trying to point.

Therefore the gesture detector needs to be conservative.

Gesture Detection Notes

The original pointing detection relied too heavily on vertical movement:

tip.y < pip.y

This caused horizontal pointing to fail.

The newer approach checks the actual index-finger direction using:

index_tip - index_mcp

This allows pointing in different horizontal/diagonal directions.

Current conceptual requirements:

Index finger extended
Other fingers folded
Finger must have enough horizontal extension
Finger should not be almost completely vertical
Reasonable tolerance for diagonal pointing

If pointing becomes too strict:

index_extended:
1.25 -> 1.10

and:

minimum_horizontal_extension:
0.55 -> 0.45

can be considered.

The maximum vertical/horizontal ratio can also be relaxed from:

2.5 -> 3.0

if necessary.

Do not make gesture recognition overly sensitive just to make one particular pose work.

Gesture Stability

Gestures should not trigger from a single frame.

The system should require a gesture to remain stable for several frames before executing it.

Current suggested values:

GLOBAL_STABLE_FRAME_REQUIREMENT = 15
DIRECTIONAL_STABLE_FRAME_REQUIREMENT = 8

Global gestures such as:

Prayer
Hang loose

should generally require more stability than directional gestures.

This helps prevent accidental commands from small tracking errors.

Current Project Structure

The project currently resembles:

Home-Automation/
│
├── main.py
│
├── hand_landmarker.task
│
├── .env
├── .gitignore
│
├── devices/
│   └── ...
│
└── vision/
    └── ...

The exact implementation may evolve.

The preferred architecture is to keep responsibilities separated.

For example:

vision/
    Hand detection
    Gesture recognition

devices/
    Kasa communication

main.py
    Application orchestration

Avoid putting all computer vision, gesture recognition, network communication, and automation logic into one enormous file.

Development Environment

Current development machine:

Windows PC
Python 3.12.x
PowerShell / Git Bash

Project location during development:

C:\Users\dylan\OneDrive\Desktop\Home-Automation

The project is being developed in:

OneDrive\Desktop

so be careful with files that are frequently modified by the development environment.

GitHub

Repository:

https://github.com/dylanflaum08/home-automation

Main branch:

main

The project has already been initialized as a Git repository and an initial commit has been created.

GitHub authentication was being configured through HTTPS.

GitHub no longer accepts normal account passwords for Git pushes.

A Personal Access Token (PAT), Git Credential Manager, GitHub CLI, or SSH authentication can be used.

Raspberry Pi Migration Plan

The PC prototype should be completed first.

Do not immediately move everything to the Pi.

Recommended migration sequence:

Phase 1 — PC Prototype

Get the following working reliably:

Webcam
Hand tracking
Pointing
Open hand
Fist
Prayer
Hang loose
Desk lamp
Cabinet lamp
Stable gesture detection
Correct directional mapping
Phase 2 — Improve Reliability

Test:

Different lighting
Different distances
Different hand angles
Both hands entering/leaving the camera
Horizontal pointing
Diagonal pointing
Partially occluded hands
Fast movement
Accidental gestures
Night/low-light conditions
Phase 3 — Raspberry Pi

Install:

Raspberry Pi OS
Python
OpenCV
MediaPipe
python-kasa
Required dependencies

Connect:

Arducam IMX290
        |
        v
Raspberry Pi 5
        |
        v
Kasa plugs
Raspberry Pi Camera Configuration

The Arducam IMX290 may require explicit camera configuration on Raspberry Pi 5.

The expected configuration from the camera documentation is along the lines of:

camera_auto_detect=0
dtoverlay=imx290

After configuration, reboot the Pi.

Do not blindly apply this configuration to another camera. It is specific to the selected IMX290 camera.

Headless Raspberry Pi Operation

The final system does not need to permanently have:

HDMI monitor
Keyboard
Mouse
Ethernet cable

The Pi should eventually operate over Wi-Fi.

Development can be done using SSH from the PC.

The final system should ideally be:

Power on
    ↓
Raspberry Pi boots
    ↓
Automation service starts
    ↓
Camera starts
    ↓
Gesture recognition starts
    ↓
System waits for commands
Future Voice Control

After gesture control is reliable, voice control is planned.

Potential architecture:

              Camera
                 |
                 v
        Gesture Recognition
                 |
                 |
Microphone --> Voice Recognition
                 |
                 v
          Command Parser
                 |
                 v
        Automation Controller
                 |
          +------+------+
          |             |
          v             v
      Desk Lamp    Cabinet Lamp

Possible voice commands could eventually include things like:

"Turn on the desk lamp"

"Turn off the cabinet lamp"

"Turn on both lights"

"Turn everything off"

Voice recognition should be added after the gesture system is stable.

Do not introduce voice complexity while the underlying device-control layer is still unreliable.

Future Smart-Home Expansion

Potential future devices:

More lights
Fans
LED strips
Bedroom lamps
Desk accessories
Other Kasa-compatible devices
Sensors
Motion detection
Temperature sensors

The goal is to make the automation layer device-agnostic where practical.

For example:

turn_on("desk_lamp")
turn_off("cabinet_lamp")
turn_on("all_lights")

would be preferable to scattering device-specific code throughout the gesture detector.

Possible Future Features

Ideas for later development:

Gesture Features
Volume control
Brightness control
Fan speed
Media controls
Custom gestures
Gesture combinations
Automation
Scheduled lighting
Motion-based automation
Sunrise/sunset behavior
Presence detection
Night mode
Voice
Natural-language commands
Device status questions
Multiple commands in one sentence

Example:

"Turn off the desk lamp and turn on the cabinet lamp."
Dashboard

Eventually a web dashboard could display:

Desk Lamp: ON
Cabinet Lamp: OFF
Camera: ACTIVE
Gesture: POINT LEFT
System: RUNNING

A small local web interface could be built using FastAPI or another lightweight framework if useful.

Important Design Principles
1. Reliability over sensitivity

It is better for a gesture to require slightly more intentional movement than for the lights to constantly trigger accidentally.

2. Keep gesture recognition separate from device control

The vision system should ideally produce a command such as:

DESK_LAMP_ON

rather than directly manipulating the Kasa plug.

This makes the system easier to test.

For example:

Camera
  ↓
Gesture Recognition
  ↓
Command
  ↓
Automation Controller
  ↓
Device Controller
  ↓
Kasa
3. Device communication should be isolated

Kasa authentication and networking should live in the device layer.

The vision code should not need to know how Kasa authentication works.

4. Do not hardcode credentials

Credentials belong in .env.

Never commit:

KASA_USERNAME
KASA_PASSWORD

or any API keys/passwords to GitHub.

5. Avoid relying on static IP addresses

The current development IPs are useful for debugging but should not be treated as permanent.

Prefer:

Kasa device discovery
DHCP reservations
Device MAC addresses
Configuration files

where appropriate.

Known Issues / Things to Watch
Kasa Authentication

Newer Kasa firmware can require KLAP v2 authentication.

Do not assume old python-kasa examples will work.

MediaPipe API

Do not copy old tutorials that use:

mp.solutions.hands

without checking the installed MediaPipe version.

The current project uses the newer Tasks API.

Pointing

Pointing must work when the finger is:

horizontal
slightly diagonal
not just pointing upward

Avoid relying solely on:

tip.y < pip.y
Hang Loose False Positives

The shaka gesture has previously been incorrectly detected during pointing.

The detector should explicitly reject a hand if it is already recognized as a pointing gesture.

Handedness

Do not assume:

MediaPipe LEFT = user's physical left hand

is enough to determine the command.

The gesture semantics should work regardless of which physical hand performs the point.

Lighting

Normal computer-vision performance can degrade significantly in darkness.

The new IMX290 camera is intended to improve low-light performance, but true darkness may still require IR illumination.

Development Philosophy

This is a personal learning project as well as a functional automation system.

The project should prioritize:

Understanding how each component works
Building incrementally
Keeping the architecture understandable
Avoiding unnecessary complexity
Testing individual components before combining them
Making the system reliable before adding flashy features

When implementing a new feature, prefer a small working change over a large rewrite.

Suggested Development Workflow

For each new feature:

1. Define the behavior
2. Identify which layer owns the behavior
3. Implement the smallest change
4. Test it independently
5. Test it with the existing system
6. Test edge cases
7. Commit the change
8. Move to the next feature
Current Priority

The immediate priority should be:

Make gesture-controlled lighting reliable on the PC

Specifically:

 Reliable hand detection
 Reliable pointing
 Open-hand + pointing = ON
 Fist + pointing = OFF
 Correct left/right lamp targeting
 Prayer = both ON
 Hang loose = both OFF
 Prevent false positives
 Require stable gestures
 Test different lighting conditions
 Test different hand angles

After that:

PC prototype
     ↓
Raspberry Pi migration
     ↓
Low-light/night testing
     ↓
Standalone operation
     ↓
Voice control
     ↓
Additional smart-home devices
Current Hardware Summary
Component	Purpose
Raspberry Pi 5 2GB	Final automation computer
CanaKit 5V/5A PSU	Raspberry Pi power
CanaKit Turbine Case	Pi enclosure
CanaKit Mega Heat Sink + Fan	Pi cooling
SanDisk Ultra 64GB microSD	Pi storage
Arducam IMX290 STARVIS	Camera
Kasa EP10P2 #1	Desk Lamp
Kasa EP10P2 #2	Cabinet Lamp
End Goal

The finished project should behave like a small standalone smart-home computer:

                    ┌─────────────────────┐
                    │    Raspberry Pi 5   │
                    │                     │
                    │  Computer Vision    │
                    │         +           │
                    │   Voice Recognition │
                    │         +           │
                    │ Automation Engine   │
                    └──────────┬──────────┘
                               │
                    Wi-Fi / Local Network
                               │
               ┌───────────────┴───────────────┐
               │                               │
               ▼                               ▼
        ┌─────────────┐                 ┌─────────────┐
        │ Desk Lamp   │                 │Cabinet Lamp │
        │ Kasa Plug   │                 │ Kasa Plug   │
        └─────────────┘                 └─────────────┘

The system should eventually be able to sit in a room, boot automatically, observe the room through the camera, recognize intentional gestures, respond to voice commands, and control smart devices without requiring the development PC to be running.