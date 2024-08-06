# Luckypot

Another pygame engine. It might be what you need, if you're lucky to be called Diego.

Seriously, you probably don't want to use this engine.
It is not stable (and I don't have plans to make it stable yet) and there are many things hardcoded for my own needs.
If you do use it, take one of those 3 options, by order of preference:
1. Copy the code and adapt it to your needs.
2. Fork it and adapt it to your needs.
3. Pin the library to a specific version, and use it as is.

There's no documentation, but the code has reasonably good docstrings.
You can also check the examples in the `examples` folder, and run them with
`python -m luckypot.examples`.


## Games made with Luckypot

Flyre a 2D shoot'em up with a skill tree: https://cozyfractal.itch.io/flyre
![Flyre](https://img.itch.zone/aW1nLzU2NDIwMDUucG5n/original/Yl3rUc.png)


## Qualty of the code

```
luckypot
├── utils.py            # 🌟 Great. Lots of nice utilites. Standalone.
├── particles.py        # 🌟 Great. If you want to do particle this specific way. Fast. Independant.
├── pygame_input.py     # 🌟 Great.
├── app.py              # 😊 Good, provided you want the same structure.
├── debug.py            # 😊 Good. Nice utility for visual debug.
├── state_machine.py    # 😊 Good. A bit bloated.
├── state_transitions.py# 😊 Good. Fun. Does the job.
├── settings.py         # 😊 Good for quick permanent saves. Edit the file directly.
├── common_objects.py   # 🤷‍ Fine. Only a health bar.
├── object.py           # 🤷‍ Fine. A bit bloated and confused. Delete stuff on reuse.
├── simple_ui.py        # 🤷‍ Fine. A few specific widget. Bad documentation.
├── assets.py           # 🤷‍ good & bad. Some nice utilities. Caching. Doesn't addapt. Confused ontologies.
├── gfx.py              # 😢 Bad. Wrapper around Surface. Not thought through. Slows things. Some nice utilities.
├── screen.py           # 😡 Terrible. Not integrated.
└── constants.py        # 😡 Terrible if you don't copy the engine folder. Otherwise fine.
```