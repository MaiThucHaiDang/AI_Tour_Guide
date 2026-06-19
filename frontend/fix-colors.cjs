const fs = require('fs');
const path = require('path');

const filesToFix = [
  'src/index.css',
  'src/components/voice/UnifiedChatPage.jsx',
  'src/components/HomeScreen.module.css',
  'src/components/dashboard/ExploreDashboard.jsx',
  'src/components/map/MapExplore.jsx',
  'src/components/game/GameHost.jsx',
  'src/components/game/GamePlayer.jsx',
  'src/components/passport/TripJournal.jsx',
  'src/components/HomeScreen.jsx'
];

filesToFix.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (!fs.existsSync(filePath)) {
    console.log(`Not found: ${file}`);
    return;
  }
  
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace white backgrounds
  content = content.replace(/background(-color)?:\s*(#fff|#ffffff|white)\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#fff8d9\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#fffaf0\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#fff3ef\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#f5f5f5\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#f8f9fa\b/gi, 'background$1: var(--color-bg-surface)');
  content = content.replace(/background(-color)?:\s*#1c1a17\b/gi, 'background$1: var(--color-bg-dark)');
  
  // Replace rgba white backgrounds (glassmorphism)
  content = content.replace(/background(-color)?:\s*rgba\(\s*255\s*,\s*255\s*,\s*255\s*,\s*[0-9.]+\s*\)/gi, 'background$1: var(--color-bg-surface-glass)');
  content = content.replace(/background(-color)?:\s*rgba\(\s*255\s*,\s*250\s*,\s*240\s*,\s*[0-9.]+\s*\)/gi, 'background$1: var(--color-bg-surface-glass)');
  
  // Replace dark texts
  content = content.replace(/color:\s*(#333|#111|#000|#101818|black)\b/gi, 'color: var(--color-text-main)');
  content = content.replace(/color:\s*(#666|#555|#4c5b57|#777|#4b5563)\b/gi, 'color: var(--color-text-muted)');
  
  // Also handle some borders
  content = content.replace(/border(-color)?:\s*#e0e0e0\b/gi, 'border$1: var(--color-border)');
  content = content.replace(/border(-color)?:\s*#e5e7eb\b/gi, 'border$1: var(--color-border)');
  content = content.replace(/border(-color)?:\s*#d1d5db\b/gi, 'border$1: var(--color-border)');

  fs.writeFileSync(filePath, content, 'utf8');
  console.log(`Fixed colors in ${file}`);
});
