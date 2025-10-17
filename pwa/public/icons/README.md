# PWA Icons

To generate PWA icons, you can use one of these methods:

## Option 1: Online Generators
- [PWA Asset Generator](https://www.pwabuilder.com/imageGenerator)
- [RealFaviconGenerator](https://realfavicongenerator.net/)

## Option 2: Using Sharp (Node.js)
```bash
npm install -g sharp-cli
sharp -i source-icon.png -o icon-72x72.png resize 72 72
sharp -i source-icon.png -o icon-96x96.png resize 96 96
sharp -i source-icon.png -o icon-128x128.png resize 128 128
sharp -i source-icon.png -o icon-144x144.png resize 144 144
sharp -i source-icon.png -o icon-152x152.png resize 152 152
sharp -i source-icon.png -o icon-192x192.png resize 192 192
sharp -i source-icon.png -o icon-384x384.png resize 384 384
sharp -i source-icon.png -o icon-512x512.png resize 512 512
```

## Required Sizes
- 72x72
- 96x96
- 128x128
- 144x144
- 152x152
- 192x192
- 384x384
- 512x512

## Icon Guidelines
- Use a simple, recognizable design
- Ensure good contrast
- Test on both light and dark backgrounds
- Consider the "safe zone" for maskable icons (80% of the image)

