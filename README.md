sudo pacman -S base-devel sdl2 sdl2_image python python-pip pkg-config

pip install gymnasium numpy pillow stable_baselines3 stable_baselines3[extra] torch tensorboard




nm -D ./SDLPoP/src/libSDLPoP.so [very useful command to find what methods are available in libSDLPop.so file, just pipe em up!]





[the steps below are not needed anymore, on arch atleast, since it's prebuilt for arch]

cd SDLPoP/src

make clean

make shared

cd ../..
