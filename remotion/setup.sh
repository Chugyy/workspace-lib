#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is required. Install via: brew install node"
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "ERROR: Node.js >= 18 required (found v$NODE_VERSION)"
    exit 1
fi

# Init npm project if needed
if [ ! -f "package.json" ]; then
    npm init -y -q 2>/dev/null
fi

# Install Remotion
npm install --save remotion @remotion/cli @remotion/bundler @remotion/renderer 2>/dev/null
npm install --save-dev typescript @types/react @types/react-dom 2>/dev/null

# Create tsconfig if missing
if [ ! -f "tsconfig.json" ]; then
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "output"]
}
EOF
fi

# Create remotion.config.ts if missing
if [ ! -f "remotion.config.ts" ]; then
    cat > remotion.config.ts << 'EOF'
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
EOF
fi

echo "remotion tool ready ($(npx remotion --version 2>/dev/null || echo 'installed'))"
