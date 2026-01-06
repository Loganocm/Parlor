const fs = require('fs');
const path = require('path');

// Load .env
const envPath = path.resolve(__dirname, '.env');
let envConfig = {};

if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, 'utf8');
  const lines = content.split(/\r?\n/); // Handle both \n and \r\n
  lines.forEach(line => {
    line = line.trim();
    if (!line || line.startsWith('#')) return; // Skip empty lines and comments

    const match = line.match(/^([^=]+)=(.*)$/);
    if (match) {
      const key = match[1].trim();
      const value = match[2].trim().replace(/^["']|["']$/g, ''); // Remove quotes if present
      envConfig[key] = value;
    }
  });
  console.log('Loaded env config keys:', Object.keys(envConfig));
}

// Merge with process.env (process.env takes precedence if set in shell)
const apiKey = process.env.GOOGLE_MAPS_API_KEY || envConfig.GOOGLE_MAPS_API_KEY || '';

if (!apiKey) {
  console.warn('⚠️  WARNING: GOOGLE_MAPS_API_KEY not found in .env or environment variables.');
} else {
  console.log('✅ Found GOOGLE_MAPS_API_KEY');
}

const targetFiles = [
  {
    template: './src/environments/environment.template.ts',
    target: './src/environments/environment.ts'
  },
  {
    template: './src/environments/environment.prod.template.ts',
    target: './src/environments/environment.prod.ts'
  }
];

targetFiles.forEach(fileConfig => {
  const templatePath = path.resolve(__dirname, fileConfig.template);
  const targetPath = path.resolve(__dirname, fileConfig.target);

  if (fs.existsSync(templatePath)) {
    let content = fs.readFileSync(templatePath, 'utf8');
    
    // Replace the placeholder
    content = content.replace('GOOGLE_MAPS_API_KEY_PLACEHOLDER', apiKey);
    
    fs.writeFileSync(targetPath, content);
    console.log(`Generated ${fileConfig.target} from template.`);
  } else {
    console.error(`Template not found: ${fileConfig.template}`);
  }
});
