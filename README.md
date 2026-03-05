# Principia: Experiments in POP using PPO.


### Currently able to get the sword!
https://github.com/user-attachments/assets/afb6e10f-2f52-48fe-a93f-be036d8e91a5

### How was the environment created?
There's this cool repo https://github.com/NagyD/SDLPoP, basically some guy just decided to disassemble and open source the OG Prince of Persia!

To create this project, i trimmed the repo to only contain the data (assets of the game) and src (logic part of game) folders along with the SDLPOP.ini (configurations eg. turning off cutscenes) file

Then using the 'make shared' command the game was compiled on arch linux, btw 
(note: you'll have to recompile the game in src/ folder if you want to run it on your machine; see the [SDLPoP Documentation](https://github.com/NagyD/SDLPoP#compiling))

Thereafter, the POP_Env.py file was created. To wrap the game around a gymnasium environment, ctypes was used to access the global variables (things like hitpoints current level, raw pixel frame, etc).

### What things does the agent 'see'
The agent has access to the 84x84 grayscaled frames and states like current level, current hitpoints, max hitpoints, possession of sword, current room index and current guard hp.

The agent makes decisions with a frame skip of 4 (since 4 is the minimum number of frames any action takes)

The agent can perform 5 actions: Up, Down, Left, Right along with one Null action.

### What rewards does the agent receive
+4 for discovering new rooms
+7 for picking up the sword
-10 for dying
+1 for health increase
-1 for health decrease
+2 for decreasing guard's hp
+3 for killing guard
-0.01 every time step (makes it kill itself if it ever gets stuck) 

### How to run it on your machine
Recompile the game as mentioned above.
Use python version 3.12.12 (might work on other python versions, haven't tested)
pip install the requirements.txt file
run the ppo.py file for single environment training.
run the multip_ppo.py file for 12 environments in parallel training.

### Notes for meself
nm -D ./SDLPoP/src/libSDLPoP.so [very useful command to find what methods are available in libSDLPop.so file, just pipe em up!]
