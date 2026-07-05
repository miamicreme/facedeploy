# Workflows

Store exported ComfyUI workflow JSON files here.

Suggested workflow stages:

1. Load video with Video Helper Suite.
2. Extract frames.
3. Load source face image.
4. Run ReActor swap.
5. Run FaceDetailer on the swapped face region.
6. Apply light restoration.
7. Recombine frames to video.
8. Use FFmpeg to copy original audio.

Start simple, confirm the nodes work, then add upscaling/color matching/interpolation only when needed.
